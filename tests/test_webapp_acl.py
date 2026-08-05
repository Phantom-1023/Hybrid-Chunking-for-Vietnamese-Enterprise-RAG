from fastapi.testclient import TestClient

from webapp.app import create_app


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_self_service_registration_profile_and_password_change(tmp_path):
    app = create_app(
        database_path=tmp_path / "webapp.db",
        token_secret="test-secret-that-is-long-and-local-only",
    )
    with TestClient(app) as client:
        registered = client.post(
            "/api/register",
            json={
                "email": "member@example.test",
                "display_name": "Member One",
                "password": "MemberPassphrase123!",
            },
        )
        assert registered.status_code == 201

        login = client.post(
            "/api/login",
            json={"email": "member@example.test", "password": "MemberPassphrase123!"},
        )
        headers = _auth(login.json()["access_token"])
        profile = client.patch("/api/profile", headers=headers, json={"display_name": "Member Two"})
        assert profile.status_code == 200
        assert profile.json()["display_name"] == "Member Two"

        changed = client.post(
            "/api/password/change", headers=headers, json={"password": "ReplacementPassphrase123!"},
        )
        assert changed.status_code == 200
        renewed_login = client.post(
            "/api/login",
            json={"email": "member@example.test", "password": "ReplacementPassphrase123!"},
        )
        assert renewed_login.status_code == 200


class _FakeReranker:
    def __init__(self):
        self.seen_titles = []

    def rerank(self, question, items, *, top_k):
        self.seen_titles = [item.metadata["title"] for item in items]
        return [
            type("Reranked", (), {"item": item, "score": 1.0})()
            for item in items[:top_k]
        ]


def test_acl_is_applied_before_search_and_admin_can_manage_users(tmp_path):
    fake_reranker = _FakeReranker()
    app = create_app(
        database_path=tmp_path / "webapp.db",
        token_secret="test-secret-that-is-long-and-local-only",
        reranker=fake_reranker,
    )
    with TestClient(app) as client:
        assert client.head("/").status_code == 200
        setup = client.post(
            "/api/setup",
            json={
                "email": "admin@example.test",
                "display_name": "Admin",
                "password": "AdminPassphrase123!",
            },
        )
        assert setup.status_code == 201
        admin_token = setup.json()["access_token"]
        admin_headers = _auth(admin_token)

        hr = client.post(
            "/api/departments", json={"name": "Nhân sự"}, headers=admin_headers
        ).json()
        finance = client.post(
            "/api/departments", json={"name": "Tài chính"}, headers=admin_headers
        ).json()

        user_response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "email": "hr@example.test",
                "display_name": "HR User",
                "password": "HrPassphrase123!",
                "role": "member",
                "department_id": hr["id"],
            },
        )
        assert user_response.status_code == 201

        manager_response = client.post(
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
        assert manager_response.status_code == 201

        client.post(
            "/api/documents",
            headers=admin_headers,
            json={
                "title": "Chính sách nhân sự",
                "content": "Nhân viên có mười hai ngày phép năm theo chính sách.",
                "access_scope": "department",
                "department_id": hr["id"],
            },
        )
        client.post(
            "/api/documents",
            headers=admin_headers,
            json={
                "title": "Ngân sách tài chính",
                "content": "Ngân sách bí mật của phòng tài chính là chín tỷ đồng.",
                "access_scope": "department",
                "department_id": finance["id"],
            },
        )

        login = client.post(
            "/api/login",
            json={"email": "hr@example.test", "password": "HrPassphrase123!"},
        )
        hr_headers = _auth(login.json()["access_token"])
        visible = client.get("/api/documents", headers=hr_headers).json()
        assert [document["title"] for document in visible] == ["Chính sách nhân sự"]

        search = client.post(
            "/api/search",
            headers=hr_headers,
            json={"question": "Ngân sách bí mật là bao nhiêu?", "top_k": 5},
        )
        assert search.status_code == 200
        body = search.json()
        assert body["retrieval"]["acl_candidates"] == 1
        assert body["retrieval"]["method"].endswith("fine_tuned_cross_encoder")
        assert fake_reranker.seen_titles == ["Chính sách nhân sự"]
        assert all(
            citation["title"] != "Ngân sách tài chính"
            for citation in body["citations"]
        )

        manager_login = client.post(
            "/api/login",
            json={
                "email": "manager@example.test",
                "password": "ManagerPassphrase123!",
            },
        )
        manager_headers = _auth(manager_login.json()["access_token"])
        organization_write = client.post(
            "/api/documents",
            headers=manager_headers,
            json={
                "title": "Thông báo toàn công ty",
                "content": "Manager không được tự nâng phạm vi tài liệu lên toàn tổ chức.",
                "access_scope": "organization",
                "department_id": None,
            },
        )
        assert organization_write.status_code == 403
