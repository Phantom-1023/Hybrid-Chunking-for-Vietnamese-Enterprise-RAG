from fastapi.testclient import TestClient

from src.hybrid_retriever import HybridResult
from webapp.app import create_app


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class _Answerer:
    configured = False

    def answer(self, *, question: str, citations: list[dict]) -> str:
        assert question and citations
        return "Local evidence answer [1]"

    def close(self):
        pass


class _RecordingHybrid:
    def __init__(self):
        self.seen_documents = []

    def retrieve(self, _question, documents, *, top_k, bm25_results):
        documents = list(documents)
        self.seen_documents = documents
        return [
            HybridResult(
                document=documents[0],
                score=0.99,
                method="hybrid_rrf",
            )
        ][:top_k]


class _BrokenHybrid:
    def retrieve(self, _question, _documents, *, top_k, bm25_results):
        raise RuntimeError("synthetic local hybrid failure")


def _setup_users(client: TestClient):
    setup = client.post(
        "/api/setup",
        json={
            "email": "admin@example.test",
            "display_name": "Admin",
            "password": "AdminPassphrase123!",
        },
    )
    admin_headers = _auth(setup.json()["access_token"])
    hr = client.post(
        "/api/departments", headers=admin_headers, json={"name": "HR"}
    ).json()
    finance = client.post(
        "/api/departments", headers=admin_headers, json={"name": "Finance"}
    ).json()
    manager = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "email": "manager@example.test",
            "display_name": "HR Manager",
            "password": "ManagerPassphrase123!",
            "role": "manager",
            "department_id": hr["id"],
        },
    )
    assert manager.status_code == 201
    uploaded_ids = {}
    for department, title, filename in (
        (hr, "HR policy", "hr.csv"),
        (finance, "Finance policy", "finance.csv"),
    ):
        uploaded = client.post(
            "/api/documents/upload",
            headers=admin_headers,
            data={
                "title": title,
                "access_scope": "department",
                "department_id": str(department["id"]),
            },
            files={
                "file": (
                    filename,
                    "topic,content\npolicy,department evidence\n",
                    "text/csv",
                )
            },
        )
        assert uploaded.status_code == 201, uploaded.text
        uploaded_ids[title] = uploaded.json()["id"]
    login = client.post(
        "/api/login",
        json={"email": "manager@example.test", "password": "ManagerPassphrase123!"},
    )
    return _auth(login.json()["access_token"]), uploaded_ids


def test_hybrid_flag_keeps_acl_before_both_retrievers_and_citations(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_UPLOAD_DIR", str(tmp_path / "uploads"))
    hybrid = _RecordingHybrid()
    app = create_app(
        database_path=tmp_path / "webapp.db",
        token_secret="test-secret-that-is-long-and-local-only",
        grounded_llm=_Answerer(),
        hybrid_retriever=hybrid,
        enable_hybrid_retrieval=True,
    )
    with TestClient(app) as client:
        manager_headers, uploaded_ids = _setup_users(client)
        response = client.post(
            "/api/search",
            headers=manager_headers,
            json={"question": "department evidence", "top_k": 5},
        )

    payload = response.json()
    assert response.status_code == 200
    assert len(hybrid.seen_documents) == 1
    assert hybrid.seen_documents[0].metadata["department_name"] == "HR"
    assert payload["retrieval"]["method"] == "hybrid_rrf"
    assert payload["citations"][0]["department"] == "HR"
    assert payload["citations"][0]["chunk_id"] == hybrid.seen_documents[0].document_id
    assert str(payload["citations"][0]["source_document_id"]) == str(
        uploaded_ids["HR policy"]
    )


def test_hybrid_failure_returns_valid_bm25_result(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_UPLOAD_DIR", str(tmp_path / "uploads"))
    app = create_app(
        database_path=tmp_path / "webapp.db",
        token_secret="test-secret-that-is-long-and-local-only",
        grounded_llm=_Answerer(),
        hybrid_retriever=_BrokenHybrid(),
        enable_hybrid_retrieval=True,
    )
    with TestClient(app) as client:
        manager_headers, _ = _setup_users(client)
        response = client.post(
            "/api/search",
            headers=manager_headers,
            json={"question": "department evidence", "top_k": 5},
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["retrieval"]["hybrid_fallback"] is True
    assert payload["retrieval"]["method"] == "bm25_acl_first"
    assert payload["citations"][0]["department"] == "HR"


def test_hybrid_without_verified_reranker_runs_rrf_without_reranking(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("WEBAPP_UPLOAD_DIR", str(tmp_path / "uploads"))
    hybrid = _RecordingHybrid()
    monkeypatch.setattr("webapp.app.HybridRetriever", lambda *, reranker: hybrid)
    app = create_app(
        database_path=tmp_path / "webapp.db",
        token_secret="test-secret-that-is-long-and-local-only",
        grounded_llm=_Answerer(),
        enable_hybrid_retrieval=True,
        enable_reranker=False,
    )
    with TestClient(app) as client:
        manager_headers, _ = _setup_users(client)
        response = client.post(
            "/api/search",
            headers=manager_headers,
            json={"question": "department evidence", "top_k": 5},
        )

    retrieval = response.json()["retrieval"]
    assert response.status_code == 200
    assert retrieval["method"] == "hybrid_rrf"
    assert retrieval["hybrid_fallback"] is False
    assert len(hybrid.seen_documents) == 1


def test_hybrid_flag_defaults_off_without_changing_bm25_contract(tmp_path, monkeypatch):
    monkeypatch.delenv("WEBAPP_ENABLE_HYBRID_RETRIEVAL", raising=False)
    monkeypatch.setenv("WEBAPP_UPLOAD_DIR", str(tmp_path / "uploads"))
    app = create_app(
        database_path=tmp_path / "webapp.db",
        token_secret="test-secret-that-is-long-and-local-only",
        hybrid_retriever=_BrokenHybrid(),
    )

    assert app.state.hybrid_enabled is False
    with TestClient(app) as client:
        manager_headers, _ = _setup_users(client)
        response = client.post(
            "/api/search",
            headers=manager_headers,
            json={"question": "department evidence", "top_k": 5},
        )

    retrieval = response.json()["retrieval"]
    assert response.status_code == 200
    assert retrieval["method"] == "bm25_acl_first"
    assert "hybrid_enabled" not in retrieval
    assert "hybrid_fallback" not in retrieval
