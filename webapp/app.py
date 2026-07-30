"""FastAPI web shell with login, admin, ACL-first search, and citations."""

from contextlib import asynccontextmanager
import hashlib
import os
from pathlib import Path
import secrets
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.bm25_retriever import BM25Retriever, LexicalDocument
from src.reranker import CrossEncoderReranker
from webapp.db import Database
from webapp.grounded_llm import GroundedLLM
from webapp.ingestion import MAX_UPLOAD_BYTES, IngestionError, extract_uploaded_document
from webapp.security import create_token, decode_token, hash_password, verify_password
from webapp.supabase_backend import SupabaseBackend, SupabaseBackendError


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
    department_id: int | str | None = None


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=80)
    role: Literal["admin", "manager", "member"] | None = None
    department_id: int | str | None = None
    is_active: bool | None = None


class DocumentCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    content: str = Field(min_length=10, max_length=200_000)
    access_scope: Literal["organization", "department", "private"]
    department_id: int | str | None = None


class DepartmentUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class MembershipCreate(BaseModel):
    user_id: int | str
    role: Literal["manager", "member"] = "member"


class MembershipUpdate(BaseModel):
    role: Literal["manager", "member"]


class DocumentUpdate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    access_scope: Literal["organization", "department", "private"]
    department_id: int | str | None = None
    label_ids: list[int | str] = Field(default_factory=list)
    grant_user_ids: list[int | str] = Field(default_factory=list)


class LabelCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    color: str = Field(default="#596780", pattern=r"^#[0-9A-Fa-f]{6}$")


class SearchRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2_000)
    top_k: int = Field(default=5, ge=1, le=5)


def create_app(
    *,
    database_path: str | Path | None = None,
    token_secret: str | None = None,
    reranker=None,
    enable_reranker: bool | None = None,
    supabase_backend: SupabaseBackend | None = None,
    grounded_llm: GroundedLLM | None = None,
) -> FastAPI:
    db = Database(
        database_path
        or os.getenv("WEBAPP_DATABASE_PATH", str(ROOT / "data" / "webapp.db"))
    )
    secret = token_secret or os.getenv("WEBAPP_TOKEN_SECRET") or secrets.token_urlsafe(48)
    backend_mode = os.getenv("WEBAPP_BACKEND", "sqlite").strip().lower()
    if supabase_backend is None and backend_mode == "supabase":
        supabase_backend = SupabaseBackend.from_environment()
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
    answerer = grounded_llm or GroundedLLM()
    upload_root = Path(os.getenv("WEBAPP_UPLOAD_DIR", str(ROOT / "data" / "webapp_uploads")))

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if supabase_backend is not None:
            supabase_backend.initialize()
        else:
            db.initialize()
        upload_root.mkdir(parents=True, exist_ok=True)
        try:
            yield
        finally:
            if supabase_backend is not None:
                supabase_backend.close()
            answerer.close()

    app = FastAPI(
        title="Vietnamese Enterprise RAG",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.db = db
    app.state.supabase_backend = supabase_backend
    app.state.token_secret = secret
    app.state.upload_root = upload_root

    @app.exception_handler(SupabaseBackendError)
    async def supabase_error_handler(
        _request: Request,
        exc: SupabaseBackendError,
    ):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    def current_user(
        authorization: Annotated[str | None, Header()] = None,
    ) -> dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        if supabase_backend is not None:
            return supabase_backend.user_from_token(authorization[7:])
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
        user["department_ids"] = db.department_ids_for_user(int(user["id"]))
        if user["department_id"] is not None:
            user["department_ids"] = list(
                dict.fromkeys([*user["department_ids"], user["department_id"]])
            )
        user["managed_department_ids"] = db.managed_department_ids_for_user(int(user["id"]))
        return user

    def require_admin(user: Annotated[dict, Depends(current_user)]) -> dict:
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Admin role required")
        return user

    def can_manage_department(user: dict, department_id: int | str | None) -> bool:
        if user["role"] == "admin":
            return True
        return department_id is not None and str(department_id) in {
            str(value) for value in user.get("managed_department_ids", [])
        }

    def require_department_manager(user: dict, department_id: int | str | None) -> None:
        if not can_manage_department(user, department_id):
            raise HTTPException(status_code=403, detail="Bạn không có quyền quản lý phòng ban này")

    def authorize_document_write(
        user: dict,
        *,
        access_scope: str,
        department_id: int | str | None,
    ) -> int | str | None:
        if user["role"] == "admin":
            if access_scope == "organization":
                return None
            if access_scope == "department" and department_id is None:
                raise HTTPException(status_code=422, detail="Tài liệu phòng ban cần chọn phòng ban")
            return department_id
        if access_scope == "organization":
            raise HTTPException(status_code=403, detail="Chỉ admin được tạo tài liệu toàn tổ chức")
        if department_id is None:
            raise HTTPException(status_code=422, detail="Chọn phòng ban quản lý tài liệu này")
        require_department_manager(user, department_id)
        return department_id

    @app.get("/api/health")
    def health():
        details = (
            supabase_backend.health_details()
            if supabase_backend is not None
            else {
                "auth": "local_pbkdf2_signed_session",
                "persistence": "sqlite",
            }
        )
        return {
            "status": "ok",
            "deployment_claim": "demo_only",
            **details,
        }

    @app.get("/api/setup/status")
    def setup_status():
        if supabase_backend is not None:
            return supabase_backend.setup_status()
        count = db.query_one("SELECT COUNT(*) AS count FROM users")
        return {"needs_setup": int(count["count"]) == 0}

    @app.post("/api/setup", status_code=status.HTTP_201_CREATED)
    def setup(
        payload: SetupRequest,
        x_bootstrap_token: Annotated[str | None, Header()] = None,
    ):
        if supabase_backend is not None:
            access_token = supabase_backend.bootstrap_admin(
                email=payload.email.lower().strip(),
                display_name=payload.display_name,
                password=payload.password,
                bootstrap_token=x_bootstrap_token,
            )
            return {"access_token": access_token, "token_type": "bearer"}
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
        if supabase_backend is not None:
            return {
                "access_token": supabase_backend.login(
                    payload.email.lower().strip(),
                    payload.password,
                ),
                "token_type": "bearer",
            }
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
        public_user = dict(user)
        public_user.pop("_access_token", None)
        return public_user

    @app.get("/api/departments")
    def departments(user: Annotated[dict, Depends(current_user)]):
        if supabase_backend is not None:
            return supabase_backend.list_departments(user["_access_token"])
        return db.query_all("SELECT * FROM departments ORDER BY name")

    @app.post("/api/departments", status_code=201)
    def create_department(
        payload: DepartmentCreate,
        admin: Annotated[dict, Depends(require_admin)],
    ):
        if supabase_backend is not None:
            department = supabase_backend.create_department(
                admin["_access_token"],
                payload.name.strip(),
            )
            supabase_backend.audit(
                admin["_access_token"],
                actor_id=str(admin["id"]),
                action="create",
                resource_type="department",
                resource_id=str(department["id"]),
                outcome="allowed",
            )
            return department
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

    @app.patch("/api/departments/{department_id}")
    def update_department(
        department_id: int | str,
        payload: DepartmentUpdate,
        admin: Annotated[dict, Depends(require_admin)],
    ):
        if supabase_backend is not None:
            department = supabase_backend.update_department(
                admin["_access_token"], str(department_id), payload.name.strip()
            )
            supabase_backend.audit(
                admin["_access_token"], actor_id=str(admin["id"]), action="update",
                resource_type="department", resource_id=str(department_id), outcome="allowed",
            )
            return department
        if not db.execute_count(
            "UPDATE departments SET name = ? WHERE id = ?", (payload.name.strip(), department_id)
        ):
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban")
        db.audit(user_id=admin["id"], action="update", resource_type="department", resource_id=str(department_id), outcome="allowed")
        return db.query_one("SELECT * FROM departments WHERE id = ?", (department_id,))

    @app.delete("/api/departments/{department_id}", status_code=204)
    def delete_department(
        department_id: int | str,
        admin: Annotated[dict, Depends(require_admin)],
    ):
        if supabase_backend is not None:
            members = supabase_backend.department_memberships(admin["_access_token"], str(department_id))
            docs = supabase_backend.documents_in_department(admin["_access_token"], str(department_id))
            if members or docs:
                raise HTTPException(status_code=409, detail="Không thể xóa phòng ban còn thành viên hoặc tài liệu")
            supabase_backend.delete_department(admin["_access_token"], str(department_id))
            supabase_backend.audit(admin["_access_token"], actor_id=str(admin["id"]), action="delete", resource_type="department", resource_id=str(department_id), outcome="allowed")
            return Response(status_code=204)
        members = db.query_one("SELECT COUNT(*) AS count FROM department_memberships WHERE department_id = ?", (department_id,))
        docs = db.query_one("SELECT COUNT(*) AS count FROM documents WHERE department_id = ?", (department_id,))
        if int(members["count"]) or int(docs["count"]):
            raise HTTPException(status_code=409, detail="Không thể xóa phòng ban còn thành viên hoặc tài liệu")
        if not db.execute_count("DELETE FROM departments WHERE id = ?", (department_id,)):
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban")
        db.audit(user_id=admin["id"], action="delete", resource_type="department", resource_id=str(department_id), outcome="allowed")
        return Response(status_code=204)

    @app.get("/api/departments/{department_id}/members")
    def list_department_members(
        department_id: int | str,
        user: Annotated[dict, Depends(current_user)],
    ):
        require_department_manager(user, department_id)
        if supabase_backend is not None:
            return supabase_backend.department_memberships(user["_access_token"], str(department_id))
        return db.query_all(
            """
            SELECT m.department_id, m.user_id, m.role, m.created_at,
                   u.display_name, u.email, u.is_active
            FROM department_memberships m JOIN users u ON u.id = m.user_id
            WHERE m.department_id = ? ORDER BY u.display_name
            """,
            (department_id,),
        )

    @app.post("/api/departments/{department_id}/members", status_code=201)
    def add_department_member(
        department_id: int | str,
        payload: MembershipCreate,
        user: Annotated[dict, Depends(current_user)],
    ):
        require_department_manager(user, department_id)
        if user["role"] != "admin" and payload.role != "member":
            raise HTTPException(status_code=403, detail="Trưởng phòng chỉ có thể thêm thành viên")
        if supabase_backend is not None:
            supabase_backend.add_membership(user["_access_token"], str(department_id), str(payload.user_id), payload.role)
            supabase_backend.audit(user["_access_token"], actor_id=str(user["id"]), action="create", resource_type="department_membership", resource_id=f"{department_id}:{payload.user_id}", outcome="allowed")
            return {"department_id": department_id, "user_id": payload.user_id, "role": payload.role}
        try:
            db.execute(
                "INSERT INTO department_memberships (department_id, user_id, role) VALUES (?, ?, ?)",
                (department_id, payload.user_id, payload.role),
            )
        except Exception as exc:
            raise HTTPException(status_code=409, detail="Thành viên đã thuộc phòng ban hoặc không tồn tại") from exc
        db.audit(user_id=user["id"], action="create", resource_type="department_membership", resource_id=f"{department_id}:{payload.user_id}", outcome="allowed")
        return {"department_id": department_id, "user_id": payload.user_id, "role": payload.role}

    @app.patch("/api/departments/{department_id}/members/{member_id}")
    def update_department_member(
        department_id: int | str,
        member_id: int | str,
        payload: MembershipUpdate,
        admin: Annotated[dict, Depends(require_admin)],
    ):
        if supabase_backend is not None:
            supabase_backend.update_membership(admin["_access_token"], str(department_id), str(member_id), payload.role)
        elif not db.execute_count(
            "UPDATE department_memberships SET role = ? WHERE department_id = ? AND user_id = ?",
            (payload.role, department_id, member_id),
        ):
            raise HTTPException(status_code=404, detail="Không tìm thấy thành viên")
        if supabase_backend is not None:
            supabase_backend.audit(admin["_access_token"], actor_id=str(admin["id"]), action="update", resource_type="department_membership", resource_id=f"{department_id}:{member_id}", outcome="allowed")
        else:
            db.audit(user_id=admin["id"], action="update", resource_type="department_membership", resource_id=f"{department_id}:{member_id}", outcome="allowed")
        return {"department_id": department_id, "user_id": member_id, "role": payload.role}

    @app.delete("/api/departments/{department_id}/members/{member_id}", status_code=204)
    def delete_department_member(
        department_id: int | str,
        member_id: int | str,
        user: Annotated[dict, Depends(current_user)],
    ):
        require_department_manager(user, department_id)
        if user["role"] != "admin" and str(member_id) == str(user["id"]):
            raise HTTPException(status_code=409, detail="Trưởng phòng không thể tự gỡ quyền quản lý")
        if supabase_backend is not None:
            supabase_backend.delete_membership(user["_access_token"], str(department_id), str(member_id))
            supabase_backend.audit(user["_access_token"], actor_id=str(user["id"]), action="delete", resource_type="department_membership", resource_id=f"{department_id}:{member_id}", outcome="allowed")
            return Response(status_code=204)
        if not db.execute_count("DELETE FROM department_memberships WHERE department_id = ? AND user_id = ?", (department_id, member_id)):
            raise HTTPException(status_code=404, detail="Không tìm thấy thành viên")
        db.audit(user_id=user["id"], action="delete", resource_type="department_membership", resource_id=f"{department_id}:{member_id}", outcome="allowed")
        return Response(status_code=204)

    @app.get("/api/users")
    def users(admin: Annotated[dict, Depends(require_admin)]):
        if supabase_backend is not None:
            return supabase_backend.list_users(admin["_access_token"])
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
        actor: Annotated[dict, Depends(current_user)],
    ):
        if actor["role"] != "admin":
            require_department_manager(actor, payload.department_id)
            if payload.role != "member":
                raise HTTPException(status_code=403, detail="Trưởng phòng chỉ có thể tạo thành viên")
        membership_role = "manager" if actor["role"] == "admin" and payload.role == "manager" else "member"
        if supabase_backend is not None:
            user_id = supabase_backend.create_user(
                email=payload.email.lower().strip(),
                display_name=payload.display_name,
                password=payload.password,
                role=payload.role,
                department_id=payload.department_id,
            )
            if payload.department_id is not None:
                supabase_backend.add_membership(
                    actor["_access_token"], str(payload.department_id), user_id, membership_role
                )
            supabase_backend.audit(
                actor["_access_token"],
                actor_id=str(actor["id"]),
                action="create",
                resource_type="user",
                resource_id=user_id,
                outcome="allowed",
            )
            return {"id": user_id}
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
        if payload.department_id is not None:
            db.execute(
                "INSERT INTO department_memberships (department_id, user_id, role) VALUES (?, ?, ?)",
                (payload.department_id, user_id, membership_role),
            )
        db.audit(
            user_id=actor["id"],
            action="create",
            resource_type="user",
            resource_id=str(user_id),
            outcome="allowed",
        )
        return {"id": user_id}

    @app.patch("/api/users/{user_id}")
    def update_user(
        user_id: int | str,
        payload: UserUpdate,
        admin: Annotated[dict, Depends(require_admin)],
    ):
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=422, detail="Không có thay đổi")
        if str(user_id) == str(admin["id"]) and updates.get("is_active") is False:
            raise HTTPException(status_code=409, detail="Không thể khóa tài khoản admin đang đăng nhập")
        if supabase_backend is not None:
            user = supabase_backend.update_profile(str(user_id), updates)
            supabase_backend.audit(admin["_access_token"], actor_id=str(admin["id"]), action="update", resource_type="user", resource_id=str(user_id), outcome="allowed")
            return user
        permitted = {"display_name", "role", "department_id", "is_active"}
        assignments = [name for name in updates if name in permitted]
        values = [updates[name] for name in assignments]
        if not assignments or not db.execute_count(
            f"UPDATE users SET {', '.join(f'{name} = ?' for name in assignments)} WHERE id = ?",
            (*values, user_id),
        ):
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        db.audit(user_id=admin["id"], action="update", resource_type="user", resource_id=str(user_id), outcome="allowed")
        return db.query_one(
            "SELECT id, email, display_name, role, department_id, is_active, created_at FROM users WHERE id = ?",
            (user_id,),
        )

    @app.get("/api/documents")
    def documents(user: Annotated[dict, Depends(current_user)]):
        rows = (
            supabase_backend.allowed_documents(user["_access_token"])
            if supabase_backend is not None
            else db.allowed_documents(user)
        )
        for row in rows:
            row.pop("content", None)
            if supabase_backend is None:
                row["labels"] = db.query_all(
                    """
                    SELECT l.id, l.name, l.color FROM document_labels l
                    JOIN document_label_links link ON link.label_id = l.id
                    WHERE link.document_id = ? ORDER BY l.name
                    """,
                    (row["id"],),
                )
        return rows

    @app.post("/api/documents", status_code=201)
    def create_document(
        payload: DocumentCreate,
        user: Annotated[dict, Depends(current_user)],
    ):
        department_id = authorize_document_write(
            user, access_scope=payload.access_scope, department_id=payload.department_id
        )
        if supabase_backend is not None:
            document_id = supabase_backend.create_document(
                user["_access_token"],
                title=payload.title.strip(),
                content=payload.content.strip(),
                access_scope=payload.access_scope,
                department_id=department_id,
                owner_id=str(user["id"]),
            )
            supabase_backend.create_document_chunks(
                str(document_id),
                [{"content": payload.content.strip(), "locator": "Nội dung nhập", "chunk_index": 0}],
            )
        else:
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
            db.execute(
                "INSERT INTO document_chunks (document_id, content, locator, chunk_index) VALUES (?, ?, ?, 0)",
                (document_id, payload.content.strip(), "Nội dung nhập"),
            )
        if supabase_backend is not None:
            supabase_backend.audit(
                user["_access_token"],
                actor_id=str(user["id"]),
                action="create",
                resource_type="document",
                resource_id=str(document_id),
                outcome="allowed",
                detail=payload.access_scope,
            )
            return {"id": document_id}
        db.audit(
            user_id=user["id"],
            action="create",
            resource_type="document",
            resource_id=str(document_id),
            outcome="allowed",
            detail=payload.access_scope,
        )
        return {"id": document_id}

    @app.post("/api/documents/upload", status_code=201)
    async def upload_document(
        file: Annotated[UploadFile, File()],
        title: Annotated[str, Form(min_length=2, max_length=200)],
        access_scope: Annotated[Literal["organization", "department", "private"], Form()],
        department_id: Annotated[str | None, Form()] = None,
        user: dict = Depends(current_user),
    ):
        payload = await file.read(MAX_UPLOAD_BYTES + 1)
        try:
            extracted = extract_uploaded_document(
                filename=file.filename or "", payload=payload, mime_type=file.content_type or ""
            )
        except IngestionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        resolved_department_id = authorize_document_write(
            user, access_scope=access_scope, department_id=department_id
        )
        checksum = hashlib.sha256(payload).hexdigest()
        # Storage object keys deliberately never contain a user-supplied file
        # name. Supabase Storage rejects some Unicode/special-character keys;
        # the original Vietnamese name remains in source_name for the UI.
        storage_name = f"{user['id']}/{secrets.token_hex(16)}{extracted.extension}"
        if supabase_backend is not None:
            document_id: str | None = None
            try:
                supabase_backend.upload_document_file(storage_name, payload, extracted.mime_type)
                document_id = supabase_backend.create_document(
                    user["_access_token"], title=title.strip(), content=extracted.content,
                    access_scope=access_scope, department_id=resolved_department_id,
                    owner_id=str(user["id"]), source_name=extracted.filename,
                    mime_type=extracted.mime_type, storage_path=storage_name, checksum=checksum,
                )
                supabase_backend.create_document_chunks(
                    str(document_id),
                    [
                        {"content": chunk.content, "locator": chunk.locator, "chunk_index": chunk.chunk_index}
                        for chunk in extracted.chunks
                    ],
                )
            except Exception:
                # The storage/object and DB writes are separate services, so
                # compensate on every failed step instead of leaving orphans.
                if document_id:
                    try:
                        supabase_backend.delete_document_as_service(str(document_id))
                    except Exception:
                        pass
                try:
                    supabase_backend.delete_document_file(storage_name)
                except Exception:
                    pass
                raise
            supabase_backend.audit(
                user["_access_token"], actor_id=str(user["id"]), action="upload",
                resource_type="document", resource_id=str(document_id), outcome="allowed",
                detail=f"chunks={len(extracted.chunks)};checksum={checksum[:12]}",
            )
        else:
            storage_path = upload_root / storage_name
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            storage_path.write_bytes(payload)
            document_id = db.execute(
                """
                INSERT INTO documents
                  (title, content, access_scope, department_id, owner_id, source_name,
                   mime_type, storage_path, processing_status, checksum, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ready', ?, CURRENT_TIMESTAMP)
                """,
                (title.strip(), extracted.content, access_scope, resolved_department_id, user["id"],
                 extracted.filename, extracted.mime_type, storage_name, checksum),
            )
            for chunk in extracted.chunks:
                db.execute(
                    "INSERT INTO document_chunks (document_id, content, locator, chunk_index) VALUES (?, ?, ?, ?)",
                    (document_id, chunk.content, chunk.locator, chunk.chunk_index),
                )
            db.audit(user_id=user["id"], action="upload", resource_type="document", resource_id=str(document_id), outcome="allowed", detail=f"chunks={len(extracted.chunks)};checksum={checksum[:12]}")
        return {
            "id": document_id, "source_name": extracted.filename,
            "chunks": len(extracted.chunks), "status": "ready",
        }

    def _allowed_document_or_404(user: dict, document_id: int | str) -> dict:
        rows = (
            supabase_backend.allowed_documents(user["_access_token"])
            if supabase_backend is not None
            else db.allowed_documents(user)
        )
        for row in rows:
            if str(row["id"]) == str(document_id):
                return row
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu trong phạm vi quyền của bạn")

    @app.get("/api/documents/{document_id}")
    def document_detail(
        document_id: int | str,
        user: Annotated[dict, Depends(current_user)],
    ):
        document = _allowed_document_or_404(user, document_id)
        document.pop("content", None)
        if supabase_backend is not None:
            chunks = supabase_backend.document_chunks(user["_access_token"], str(document_id))
        else:
            chunks = db.query_all(
                "SELECT id, locator, chunk_index, content FROM document_chunks WHERE document_id = ? ORDER BY chunk_index",
                (document_id,),
            )
        document["chunks"] = chunks
        return document

    @app.get("/api/documents/{document_id}/download")
    def download_document(
        document_id: int | str,
        user: Annotated[dict, Depends(current_user)],
    ):
        document = _allowed_document_or_404(user, document_id)
        storage_name = document.get("storage_path") or ""
        if not storage_name:
            raise HTTPException(status_code=404, detail="Tài liệu cũ không có file gốc để tải")
        if supabase_backend is not None:
            return RedirectResponse(supabase_backend.signed_document_url(storage_name), status_code=307)
        file_path = (upload_root / storage_name).resolve()
        if upload_root.resolve() not in file_path.parents or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Không tìm thấy file gốc")
        return FileResponse(file_path, filename=document.get("source_name") or document["title"])

    @app.delete("/api/documents/{document_id}", status_code=204)
    def delete_document(
        document_id: int | str,
        user: Annotated[dict, Depends(current_user)],
    ):
        document = _allowed_document_or_404(user, document_id)
        require_department_manager(user, document.get("department_id"))
        if supabase_backend is not None:
            supabase_backend.delete_document(user["_access_token"], str(document_id))
            if document.get("storage_path"):
                supabase_backend.delete_document_file(str(document["storage_path"]))
            supabase_backend.audit(user["_access_token"], actor_id=str(user["id"]), action="delete", resource_type="document", resource_id=str(document_id), outcome="allowed")
            return Response(status_code=204)
        storage_name = document.get("storage_path") or ""
        if not db.execute_count("DELETE FROM documents WHERE id = ?", (document_id,)):
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        if storage_name:
            file_path = (upload_root / storage_name).resolve()
            if upload_root.resolve() in file_path.parents and file_path.is_file():
                file_path.unlink()
        db.audit(user_id=user["id"], action="delete", resource_type="document", resource_id=str(document_id), outcome="allowed")
        return Response(status_code=204)

    @app.get("/api/labels")
    def list_labels(user: Annotated[dict, Depends(current_user)]):
        if supabase_backend is not None:
            return supabase_backend.labels(user["_access_token"])
        return db.query_all("SELECT * FROM document_labels ORDER BY name")

    @app.post("/api/labels", status_code=201)
    def create_label(
        payload: LabelCreate,
        admin: Annotated[dict, Depends(require_admin)],
    ):
        if supabase_backend is not None:
            label = supabase_backend.create_label(admin["_access_token"], payload.name.strip(), payload.color)
            supabase_backend.audit(admin["_access_token"], actor_id=str(admin["id"]), action="create", resource_type="document_label", resource_id=str(label["id"]), outcome="allowed")
            return label
        try:
            label_id = db.execute("INSERT INTO document_labels (name, color) VALUES (?, ?)", (payload.name.strip(), payload.color))
        except Exception as exc:
            raise HTTPException(status_code=409, detail="Nhãn đã tồn tại") from exc
        db.audit(user_id=admin["id"], action="create", resource_type="document_label", resource_id=str(label_id), outcome="allowed")
        return db.query_one("SELECT * FROM document_labels WHERE id = ?", (label_id,))

    @app.patch("/api/documents/{document_id}")
    def update_document(
        document_id: int | str,
        payload: DocumentUpdate,
        user: Annotated[dict, Depends(current_user)],
    ):
        _allowed_document_or_404(user, document_id)
        department_id = authorize_document_write(
            user, access_scope=payload.access_scope, department_id=payload.department_id
        )
        grant_user_ids = payload.grant_user_ids if payload.access_scope == "private" else []
        if supabase_backend is not None:
            document = supabase_backend.update_document(
                user["_access_token"], str(document_id), title=payload.title.strip(),
                access_scope=payload.access_scope, department_id=department_id,
            )
            supabase_backend.replace_document_labels(str(document_id), [str(value) for value in payload.label_ids])
            supabase_backend.replace_document_grants(str(document_id), [str(value) for value in grant_user_ids])
            supabase_backend.audit(user["_access_token"], actor_id=str(user["id"]), action="update", resource_type="document", resource_id=str(document_id), outcome="allowed")
            return document
        if not db.execute_count(
            "UPDATE documents SET title = ?, access_scope = ?, department_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload.title.strip(), payload.access_scope, department_id, document_id),
        ):
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        db.execute("DELETE FROM document_label_links WHERE document_id = ?", (document_id,))
        for label_id in payload.label_ids:
            db.execute("INSERT INTO document_label_links (document_id, label_id) VALUES (?, ?)", (document_id, label_id))
        db.execute("DELETE FROM document_access_grants WHERE document_id = ?", (document_id,))
        for granted_user_id in grant_user_ids:
            db.execute("INSERT INTO document_access_grants (document_id, user_id) VALUES (?, ?)", (document_id, granted_user_id))
        db.audit(user_id=user["id"], action="update", resource_type="document", resource_id=str(document_id), outcome="allowed")
        return _allowed_document_or_404(user, document_id)

    @app.post("/api/search")
    def search(
        payload: SearchRequest,
        user: Annotated[dict, Depends(current_user)],
    ):
        allowed_chunks = (
            supabase_backend.allowed_document_chunks(user["_access_token"])
            if supabase_backend is not None
            else db.allowed_document_chunks(user)
        )
        if not allowed_chunks:
            if supabase_backend is not None:
                supabase_backend.audit(
                    user["_access_token"],
                    actor_id=str(user["id"]),
                    action="search",
                    resource_type="document",
                    outcome="allowed_empty",
                )
            else:
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
                document_id=str(chunk["id"]),
                content=chunk["content"],
                metadata=chunk,
            )
            for chunk in allowed_chunks
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
                "document_id": document.document_id,
                "chunk_id": document.document_id,
                "source_document_id": document.metadata["document_id"],
                "title": document.metadata["title"],
                "source_name": document.metadata.get("source_name") or document.metadata["title"],
                "department": document.metadata["department_name"],
                "access_scope": document.metadata["access_scope"],
                "locator": document.metadata.get("locator") or "Nội dung",
                "score": score,
                "excerpt": document.content[:900],
            }
            for document, score in evidence_documents
        ]
        if supabase_backend is not None:
            supabase_backend.audit(
                user["_access_token"],
                actor_id=str(user["id"]),
                action="search",
                resource_type="document",
                outcome="allowed",
                detail=f"acl_candidates={len(allowed_chunks)};evidence={len(citations)}",
            )
        else:
            db.audit(
                user_id=user["id"],
                action="search",
                resource_type="document",
                outcome="allowed",
                detail=f"acl_candidates={len(allowed_chunks)};evidence={len(citations)}",
            )
        return {
            "answer": answerer.answer(question=payload.question, citations=citations),
            "citations": citations,
            "retrieval": {
                "acl_candidates": len(allowed_chunks),
                "method": method,
                "candidate_k": min(20, len(allowed_chunks)),
                "evidence_k": len(citations),
                "generator": "deepseek_grounded" if answerer.configured else "evidence_only",
            },
        }

    @app.get("/api/audit")
    def audit_log(admin: Annotated[dict, Depends(require_admin)]):
        if supabase_backend is not None:
            return supabase_backend.audit_logs(admin["_access_token"])
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

    @app.head("/", include_in_schema=False)
    def index_health_probe():
        return Response(status_code=200)

    return app


app = create_app()
