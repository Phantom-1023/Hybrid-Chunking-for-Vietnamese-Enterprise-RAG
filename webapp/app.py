"""FastAPI web shell with login, admin, ACL-first search, and citations."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
import secrets
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.bm25_retriever import BM25Retriever, LexicalDocument
from src.reranker import CrossEncoderReranker
from webapp.db import Database
from webapp.security import create_token, decode_token, hash_password, verify_password


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"


class SetupRequest(BaseModel):
    email: str
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=10, max_length=200)


class LoginRequest(BaseModel):
    email: str
    password: str


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class UserCreate(BaseModel):
    email: str
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=10, max_length=200)
    role: Literal["admin", "manager", "member"] = "member"
    department_id: int | None = None


class DocumentCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    content: str = Field(min_length=10, max_length=200_000)
    access_scope: Literal["organization", "department", "private"]
    department_id: int | None = None


class SearchRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2_000)
    top_k: int = Field(default=5, ge=1, le=5)


def create_app(
    *,
    database_path: str | Path | None = None,
    token_secret: str | None = None,
    reranker=None,
    enable_reranker: bool | None = None,
) -> FastAPI:
    db = Database(
        database_path
        or os.getenv("WEBAPP_DATABASE_PATH", str(ROOT / "data" / "webapp.db"))
    )
    secret = token_secret or os.getenv("WEBAPP_TOKEN_SECRET") or secrets.token_urlsafe(48)
    should_load_reranker = (
        enable_reranker
        if enable_reranker is not None
        else os.getenv("WEBAPP_ENABLE_RERANKER", "false").lower() == "true"
    )
    if reranker is None and should_load_reranker:
        checkpoint_path = ROOT / "checkpoints" / "reranker" / "full" / "best"
        checksum_path = ROOT / "artifacts" / "reranker" / "full_checkpoint.sha256"
        if not checkpoint_path.is_dir() or not checksum_path.is_file():
            raise RuntimeError("Fine-tuned reranker is enabled but checkpoint is missing")
        expected_checksum = checksum_path.read_text(encoding="utf-8").split()[0]
        reranker = CrossEncoderReranker(
            checkpoint_path,
            expected_sha256=expected_checksum,
            device=os.getenv("RERANKER_DEVICE", "cpu"),
        )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        db.initialize()
        yield

    app = FastAPI(
        title="Vietnamese Enterprise RAG",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.db = db
    app.state.token_secret = secret

    def current_user(
        authorization: Annotated[str | None, Header()] = None,
    ) -> dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        try:
            user_id = decode_token(authorization[7:], secret)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        user = db.query_one(
            """
            SELECT u.*, d.name AS department_name
            FROM users u LEFT JOIN departments d ON d.id = u.department_id
            WHERE u.id = ? AND u.is_active = 1
            """,
            (user_id,),
        )
        if not user:
            raise HTTPException(status_code=401, detail="User is inactive or missing")
        user.pop("password_hash", None)
        return user

    def require_admin(user: Annotated[dict, Depends(current_user)]) -> dict:
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Admin role required")
        return user

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "auth": "local_pbkdf2_signed_session",
            "deployment_claim": "demo_only",
        }

    @app.get("/api/setup/status")
    def setup_status():
        count = db.query_one("SELECT COUNT(*) AS count FROM users")
        return {"needs_setup": int(count["count"]) == 0}

    @app.post("/api/setup", status_code=status.HTTP_201_CREATED)
    def setup(payload: SetupRequest):
        count = db.query_one("SELECT COUNT(*) AS count FROM users")
        if int(count["count"]) > 0:
            raise HTTPException(status_code=409, detail="Setup already completed")
        admin_id = db.execute(
            """
            INSERT INTO users (email, display_name, password_hash, role)
            VALUES (?, ?, ?, 'admin')
            """,
            (payload.email.lower().strip(), payload.display_name, hash_password(payload.password)),
        )
        db.audit(
            user_id=admin_id,
            action="bootstrap",
            resource_type="user",
            resource_id=str(admin_id),
            outcome="allowed",
        )
        return {"access_token": create_token(admin_id, secret), "token_type": "bearer"}

    @app.post("/api/login")
    def login(payload: LoginRequest):
        user = db.query_one(
            "SELECT * FROM users WHERE email = ? AND is_active = 1",
            (payload.email.lower().strip(),),
        )
        if not user or not verify_password(payload.password, user["password_hash"]):
            db.audit(
                user_id=user["id"] if user else None,
                action="login",
                resource_type="session",
                outcome="denied",
            )
            raise HTTPException(status_code=401, detail="Email or password is incorrect")
        db.audit(
            user_id=user["id"],
            action="login",
            resource_type="session",
            outcome="allowed",
        )
        return {
            "access_token": create_token(user["id"], secret),
            "token_type": "bearer",
        }

    @app.get("/api/me")
    def me(user: Annotated[dict, Depends(current_user)]):
        return user

    @app.get("/api/departments")
    def departments(user: Annotated[dict, Depends(current_user)]):
        return db.query_all("SELECT * FROM departments ORDER BY name")

    @app.post("/api/departments", status_code=201)
    def create_department(
        payload: DepartmentCreate,
        admin: Annotated[dict, Depends(require_admin)],
    ):
        try:
            department_id = db.execute(
                "INSERT INTO departments (name) VALUES (?)", (payload.name.strip(),)
            )
        except Exception as exc:
            raise HTTPException(status_code=409, detail="Department already exists") from exc
        db.audit(
            user_id=admin["id"],
            action="create",
            resource_type="department",
            resource_id=str(department_id),
            outcome="allowed",
        )
        return db.query_one("SELECT * FROM departments WHERE id = ?", (department_id,))

    @app.get("/api/users")
    def users(admin: Annotated[dict, Depends(require_admin)]):
        return db.query_all(
            """
            SELECT u.id, u.email, u.display_name, u.role, u.department_id,
                   u.is_active, u.created_at, d.name AS department_name
            FROM users u LEFT JOIN departments d ON d.id = u.department_id
            ORDER BY u.id
            """
        )

    @app.post("/api/users", status_code=201)
    def create_user(
        payload: UserCreate,
        admin: Annotated[dict, Depends(require_admin)],
    ):
        try:
            user_id = db.execute(
                """
                INSERT INTO users
                    (email, display_name, password_hash, role, department_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    payload.email.lower().strip(),
                    payload.display_name,
                    hash_password(payload.password),
                    payload.role,
                    payload.department_id,
                ),
            )
        except Exception as exc:
            raise HTTPException(status_code=409, detail="User could not be created") from exc
        db.audit(
            user_id=admin["id"],
            action="create",
            resource_type="user",
            resource_id=str(user_id),
            outcome="allowed",
        )
        return {"id": user_id}

    @app.get("/api/documents")
    def documents(user: Annotated[dict, Depends(current_user)]):
        return db.allowed_documents(user)

    @app.post("/api/documents", status_code=201)
    def create_document(
        payload: DocumentCreate,
        user: Annotated[dict, Depends(current_user)],
    ):
        if user["role"] not in {"admin", "manager"}:
            raise HTTPException(status_code=403, detail="Manager or admin role required")
        department_id = payload.department_id
        if payload.access_scope == "department":
            department_id = department_id or user["department_id"]
            if department_id is None:
                raise HTTPException(status_code=422, detail="Department is required")
            if user["role"] != "admin" and department_id != user["department_id"]:
                raise HTTPException(status_code=403, detail="Cross-department write denied")
        document_id = db.execute(
            """
            INSERT INTO documents
                (title, content, access_scope, department_id, owner_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload.title.strip(),
                payload.content.strip(),
                payload.access_scope,
                department_id,
                user["id"],
            ),
        )
        db.audit(
            user_id=user["id"],
            action="create",
            resource_type="document",
            resource_id=str(document_id),
            outcome="allowed",
            detail=payload.access_scope,
        )
        return {"id": document_id}

    @app.post("/api/search")
    def search(
        payload: SearchRequest,
        user: Annotated[dict, Depends(current_user)],
    ):
        allowed = db.allowed_documents(user)
        if not allowed:
            db.audit(
                user_id=user["id"],
                action="search",
                resource_type="document",
                outcome="allowed_empty",
            )
            return {
                "answer": "Chưa có tài liệu nào bạn được phép truy cập.",
                "citations": [],
                "retrieval": {"acl_candidates": 0, "method": "bm25_acl_first"},
            }
        documents_for_ranker = [
            LexicalDocument(
                document_id=str(document["id"]),
                content=document["content"],
                metadata=document,
            )
            for document in allowed
        ]
        ranked = BM25Retriever(documents_for_ranker).retrieve(
            payload.question,
            top_k=min(20, len(documents_for_ranker)),
        )
        if reranker is not None:
            evidence = reranker.rerank(
                payload.question,
                [item.document for item in ranked],
                top_k=payload.top_k,
            )
            evidence_documents = [
                (item.item, item.score) for item in evidence
            ]
            method = "bm25_acl_first_then_fine_tuned_cross_encoder"
        else:
            evidence_documents = [
                (item.document, item.score) for item in ranked[: payload.top_k]
            ]
            method = "bm25_acl_first"
        citations = [
            {
                "document_id": int(document.document_id),
                "title": document.metadata["title"],
                "department": document.metadata["department_name"],
                "access_scope": document.metadata["access_scope"],
                "score": score,
                "excerpt": document.content[:700],
            }
            for document, score in evidence_documents
        ]
        db.audit(
            user_id=user["id"],
            action="search",
            resource_type="document",
            outcome="allowed",
            detail=f"acl_candidates={len(allowed)};evidence={len(citations)}",
        )
        return {
            "answer": (
                "Đây là các đoạn bằng chứng phù hợp nhất trong phạm vi quyền truy cập "
                "của bạn. Bản demo không tự bịa câu trả lời khi chưa cấu hình LLM."
            ),
            "citations": citations,
            "retrieval": {
                "acl_candidates": len(allowed),
                "method": method,
                "candidate_k": min(20, len(allowed)),
                "evidence_k": len(citations),
            },
        }

    @app.get("/api/audit")
    def audit_log(admin: Annotated[dict, Depends(require_admin)]):
        return db.query_all(
            """
            SELECT a.*, u.email
            FROM audit_log a LEFT JOIN users u ON u.id = a.user_id
            ORDER BY a.id DESC LIMIT 200
            """
        )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
