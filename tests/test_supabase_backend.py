import json

import httpx
from fastapi.testclient import TestClient

from webapp.app import create_app
from webapp.supabase_backend import SupabaseBackend


class _RerankerSpy:
    def __init__(self):
        self.seen_document_ids = []

    def rerank(self, question, items, *, top_k):
        self.seen_document_ids = [item.document_id for item in items]
        return [
            type("Reranked", (), {"item": item, "score": 0.9})()
            for item in items[:top_k]
        ]


def _json_response(payload, status_code=200):
    return httpx.Response(
        status_code,
        content=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
    )


def test_supabase_user_token_drives_rls_before_reranking(tmp_path):
    requests = []

    def handler(request: httpx.Request):
        requests.append(request)
        if request.url.path == "/auth/v1/token":
            return _json_response({"access_token": "user-access-token"})
        if request.url.path == "/auth/v1/user":
            return _json_response({"id": "user-hr"})
        if request.url.path == "/rest/v1/profiles":
            return _json_response(
                [
                    {
                        "id": "user-hr",
                        "email": "hr@example.test",
                        "display_name": "HR User",
                        "role": "member",
                        "department_id": "department-hr",
                        "created_at": "2026-07-30T00:00:00Z",
                        "departments": {"name": "Nhân sự"},
                    }
                ]
            )
        if request.url.path == "/rest/v1/department_memberships":
            return _json_response([])
        if request.url.path == "/rest/v1/document_chunks":
            # Simulates chunks that Postgres RLS permits for this bearer.
            return _json_response(
                [
                    {
                        "id": "chunk-hr-1",
                        "document_id": "document-hr",
                        "content": "Nhân viên có mười hai ngày phép năm.",
                        "locator": "Trang 1",
                        "chunk_index": 0,
                        "documents": {
                            "id": "document-hr",
                            "title": "Chính sách nhân sự",
                            "source_name": "chinh-sach-nhan-su.pdf",
                            "scope": "department",
                            "department_id": "department-hr",
                            "departments": {"name": "Nhân sự"},
                        },
                    }
                ]
            )
        if request.url.path == "/rest/v1/documents":
            # Simulates the rows that Postgres RLS permits for this bearer.
            return _json_response(
                [
                    {
                        "id": "document-hr",
                        "title": "Chính sách nhân sự",
                        "content": "Nhân viên có mười hai ngày phép năm.",
                        "scope": "department",
                        "department_id": "department-hr",
                        "owner_id": "admin-user",
                        "created_at": "2026-07-30T00:00:00Z",
                        "departments": {"name": "Nhân sự"},
                    }
                ]
            )
        if request.url.path == "/rest/v1/rpc/append_audit_event":
            return _json_response([], status_code=201)
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    backend = SupabaseBackend(
        "https://project.example.test",
        "anon-test-key",
        service_role_key="service-test-key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    reranker = _RerankerSpy()
    app = create_app(
        database_path=tmp_path / "unused.db",
        supabase_backend=backend,
        reranker=reranker,
    )

    with TestClient(app) as client:
        health = client.get("/api/health").json()
        assert health["auth"] == "supabase_auth"
        assert health["persistence"] == "supabase_postgres_rls"

        login = client.post(
            "/api/login",
            json={"email": "hr@example.test", "password": "Passphrase123!"},
        )
        assert login.status_code == 200
        headers = {"Authorization": "Bearer user-access-token"}

        response = client.post(
            "/api/search",
            headers=headers,
            json={"question": "Chính sách nghỉ phép?", "top_k": 5},
        )
        assert response.status_code == 200
        assert response.json()["retrieval"]["acl_candidates"] == 1
        assert reranker.seen_document_ids == ["chunk-hr-1"]

    rls_requests = [
        request
        for request in requests
        if request.url.path in {
            "/rest/v1/profiles",
            "/rest/v1/department_memberships",
            "/rest/v1/document_chunks",
        }
    ]
    assert rls_requests
    assert all(
        request.headers["authorization"] == "Bearer user-access-token"
        for request in rls_requests
    )
    assert all(
        request.headers["authorization"] != "Bearer service-test-key"
        for request in rls_requests
    )


def test_supabase_setup_is_disabled_without_server_admin_key():
    backend = SupabaseBackend(
        "https://project.example.test",
        "anon-test-key",
        client=httpx.Client(transport=httpx.MockTransport(lambda _: _json_response([]))),
    )
    assert backend.setup_status() == {
        "needs_setup": False,
        "admin_setup_available": False,
    }


def test_new_opaque_secret_key_is_not_misused_as_user_bearer():
    captured = []

    def handler(request: httpx.Request):
        captured.append(request)
        return _json_response([])

    backend = SupabaseBackend(
        "https://project.example.test",
        "sb_publishable_example",
        service_role_key="sb_secret_example",
        bootstrap_token="one-time-bootstrap-token",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    status = backend.setup_status()
    assert status == {"needs_setup": True, "admin_setup_available": True}
    assert captured[0].headers["apikey"] == "sb_secret_example"
    assert "authorization" not in captured[0].headers


def test_document_write_uses_authenticated_authorization_rpc():
    captured = []

    def handler(request: httpx.Request):
        captured.append(request)
        return _json_response("document-1", status_code=200)

    backend = SupabaseBackend(
        "https://project.example.test",
        "anon-test-key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    document_id = backend.create_document(
        "user-access-token",
        title="Tài liệu kiểm thử",
        content="Nội dung kiểm thử",
        access_scope="department",
        department_id="department-hr",
        owner_id="user-hr",
    )

    assert document_id == "document-1"
    assert captured[0].url.path == "/rest/v1/rpc/create_authorized_document"
    assert captured[0].headers["authorization"] == "Bearer user-access-token"
