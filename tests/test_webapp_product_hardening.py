from __future__ import annotations

from fastapi.testclient import TestClient

from webapp.app import create_app


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class _Answerer:
    configured = True

    def answer(self, *, question: str, citations: list[dict]) -> str:
        assert question
        assert citations
        return "Nhân viên có mười hai ngày phép. [1]"

    def close(self) -> None:
        pass


def _setup(client: TestClient) -> tuple[dict[str, str], int, int]:
    admin = client.post(
        "/api/setup",
        json={
            "email": "admin@example.test",
            "display_name": "Admin",
            "password": "AdminPassphrase123!",
        },
    )
    headers = _auth(admin.json()["access_token"])
    hr = client.post("/api/departments", headers=headers, json={"name": "Nhân sự"}).json()
    finance = client.post("/api/departments", headers=headers, json={"name": "Tài chính"}).json()
    manager = client.post(
        "/api/users",
        headers=headers,
        json={
            "email": "manager@example.test",
            "display_name": "HR Manager",
            "password": "ManagerPassphrase123!",
            "role": "manager",
            "department_id": hr["id"],
        },
    )
    assert manager.status_code == 201
    return headers, hr["id"], finance["id"]


def test_public_registration_is_disabled_by_default_and_explicit_when_enabled(tmp_path):
    disabled = create_app(
        database_path=tmp_path / "disabled.db",
        token_secret="test-secret-that-is-long-and-local-only",
    )
    with TestClient(disabled) as client:
        assert client.get("/api/setup/status").json()["public_registration_enabled"] is False
        response = client.post(
            "/api/register",
            json={"email": "new@example.test", "display_name": "New User", "password": "Passphrase123!"},
        )
        assert response.status_code == 403

    enabled = create_app(
        database_path=tmp_path / "enabled.db",
        token_secret="test-secret-that-is-long-and-local-only",
        allow_public_registration=True,
    )
    with TestClient(enabled) as client:
        assert client.get("/api/setup/status").json()["public_registration_enabled"] is True
        response = client.post(
            "/api/register",
            json={"email": "new@example.test", "display_name": "New User", "password": "Passphrase123!"},
        )
        assert response.status_code == 201


def test_manager_uploads_csv_and_citation_opens_original_file(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_UPLOAD_DIR", str(tmp_path / "uploads"))
    app = create_app(
        database_path=tmp_path / "webapp.db",
        token_secret="test-secret-that-is-long-and-local-only",
        grounded_llm=_Answerer(),
    )
    with TestClient(app) as client:
        admin_headers, hr_id, _ = _setup(client)
        login = client.post(
            "/api/login",
            json={"email": "manager@example.test", "password": "ManagerPassphrase123!"},
        )
        manager_headers = _auth(login.json()["access_token"])

        upload = client.post(
            "/api/documents/upload",
            headers=manager_headers,
            data={"title": "Chính sách phép", "access_scope": "department", "department_id": str(hr_id)},
            files={"file": ("phep.csv", "Loai,So ngay\nPhep nam,12\n", "text/csv")},
        )
        assert upload.status_code == 201, upload.text
        document_id = upload.json()["id"]
        assert upload.json()["chunks"] == 1

        answer = client.post(
            "/api/search", headers=manager_headers,
            json={"question": "Có bao nhiêu ngày phép năm?", "top_k": 5},
        )
        assert answer.status_code == 200
        body = answer.json()
        assert body["answer"].endswith("[1]")
        assert body["retrieval"]["generator"] == "deepseek_grounded"
        assert body["citations"][0]["source_document_id"] == document_id
        assert body["citations"][0]["locator"] == "CSV, hàng 2"

        detail = client.get(f"/api/documents/{document_id}", headers=manager_headers)
        assert detail.status_code == 200
        assert detail.json()["chunks"][0]["locator"] == "CSV, hàng 2"
        original = client.get(f"/api/documents/{document_id}/download", headers=manager_headers)
        assert original.status_code == 200
        assert b"Phep nam" in original.content

        vietnamese_name = "de-an & ban nhap.txt"
        unicode_upload = client.post(
            "/api/documents/upload",
            headers=manager_headers,
            data={"title": "Tài liệu tiếng Việt", "access_scope": "department", "department_id": str(hr_id)},
            files={"file": (vietnamese_name, "Nội dung thử nghiệm", "text/plain")},
        )
        assert unicode_upload.status_code == 201, unicode_upload.text
        unicode_id = unicode_upload.json()["id"]
        unicode_detail = client.get(f"/api/documents/{unicode_id}", headers=manager_headers).json()
        assert unicode_detail["source_name"] == vietnamese_name
        stored_names = [path.name for path in (tmp_path / "uploads").rglob("*") if path.is_file()]
        assert all(name.isascii() for name in stored_names)

        forbidden = client.post(
            "/api/documents/upload",
            headers=manager_headers,
            data={"title": "Không được phép", "access_scope": "organization"},
            files={"file": ("x.txt", b"No", "text/plain")},
        )
        assert forbidden.status_code == 403


def test_restricted_document_requires_explicit_grant_and_manager_is_scoped(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_UPLOAD_DIR", str(tmp_path / "uploads"))
    app = create_app(
        database_path=tmp_path / "webapp.db",
        token_secret="test-secret-that-is-long-and-local-only",
        grounded_llm=_Answerer(),
    )
    with TestClient(app) as client:
        admin_headers, hr_id, finance_id = _setup(client)
        member = client.post(
            "/api/users", headers=admin_headers,
            json={
                "email": "member@example.test", "display_name": "HR Member",
                "password": "MemberPassphrase123!", "role": "member", "department_id": hr_id,
            },
        )
        finance_member = client.post(
            "/api/users", headers=admin_headers,
            json={
                "email": "finance@example.test", "display_name": "Finance Member",
                "password": "FinancePassphrase123!", "role": "member", "department_id": finance_id,
            },
        )
        assert member.status_code == finance_member.status_code == 201
        manager_login = client.post("/api/login", json={"email": "manager@example.test", "password": "ManagerPassphrase123!"})
        manager_headers = _auth(manager_login.json()["access_token"])

        cross_department_member = client.post(
            f"/api/departments/{finance_id}/members",
            headers=manager_headers,
            json={"user_id": finance_member.json()["id"], "role": "member"},
        )
        assert cross_department_member.status_code == 403

        upload = client.post(
            "/api/documents/upload", headers=manager_headers,
            data={"title": "Lương lãnh đạo", "access_scope": "private", "department_id": str(hr_id)},
            files={"file": ("luong.txt", "Lương lãnh đạo là dữ liệu hạn chế.", "text/plain")},
        )
        assert upload.status_code == 201, upload.text
        document_id = upload.json()["id"]

        member_login = client.post("/api/login", json={"email": "member@example.test", "password": "MemberPassphrase123!"})
        member_headers = _auth(member_login.json()["access_token"])
        assert client.get("/api/documents", headers=member_headers).json() == []

        updated = client.patch(
            f"/api/documents/{document_id}", headers=manager_headers,
            json={
                "title": "Lương lãnh đạo", "access_scope": "private", "department_id": hr_id,
                "label_ids": [], "grant_user_ids": [member.json()["id"]],
            },
        )
        assert updated.status_code == 200, updated.text
        member_docs = client.get("/api/documents", headers=member_headers).json()
        assert [doc["id"] for doc in member_docs] == [document_id]

        finance_login = client.post("/api/login", json={"email": "finance@example.test", "password": "FinancePassphrase123!"})
        finance_headers = _auth(finance_login.json()["access_token"])
        assert client.get("/api/documents", headers=finance_headers).json() == []
        assert client.get(f"/api/documents/{document_id}", headers=finance_headers).status_code == 404
