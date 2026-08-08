from fastapi.testclient import TestClient

from webapp.app import create_app


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_self_service_registration_profile_and_password_change(tmp_path):
    app = create_app(
        database_path=tmp_path / "webapp.db",
        token_secret="test-secret-that-is-long-and-local-only",
        allow_public_registration=True,
    )
    with TestClient(app) as client:
        assert client.get("/api/setup/status").json()["public_registration_enabled"] is True
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


def test_public_registration_is_disabled_by_default(tmp_path):
    app = create_app(
        database_path=tmp_path / "webapp.db",
        token_secret="test-secret-that-is-long-and-local-only",
    )
    with TestClient(app) as client:
        assert client.get("/api/setup/status").json()["public_registration_enabled"] is False
        response = client.post(
            "/api/register",
            json={
                "email": "member@example.test",
                "display_name": "Member One",
                "password": "MemberPassphrase123!",
            },
        )
        assert response.status_code == 403
        assert "quản trị viên" in response.json()["detail"]


def test_admin_user_directory_is_paginated_and_supports_safe_account_actions(tmp_path):
    app = create_app(database_path=tmp_path / "webapp.db", token_secret="test-secret-that-is-long-and-local-only")
    with TestClient(app) as client:
        setup = client.post("/api/setup", json={"email": "admin@example.test", "display_name": "Admin", "password": "AdminPassphrase123!"})
        headers = _auth(setup.json()["access_token"])
        department = client.post("/api/departments", headers=headers, json={"name": "Operations", "description": "Runs operations"}).json()
        for number in range(12):
            response = client.post("/api/users", headers=headers, json={
                "email": f"member{number}@example.test", "display_name": f"Member {number}",
                "password": "MemberPassphrase123!", "role": "member", "department_id": department["id"],
            })
            assert response.status_code == 201
        directory = client.get("/api/users?page=2&page_size=10&search=member", headers=headers)
        assert directory.status_code == 200
        assert directory.json()["total"] == 12
        assert len(directory.json()["items"]) == 2
        target = directory.json()["items"][0]
        assert target["employee_code"].startswith("PB-")
        assert client.patch(f"/api/users/{target['id']}", headers=headers, json={"is_active": False}).status_code == 200
        assert client.post(f"/api/users/{target['id']}/password", headers=headers, json={"password": "ReplacementPassphrase123!"}).status_code == 200
        detail = client.get(f"/api/users/{target['id']}", headers=headers)
        assert detail.status_code == 200
        assert "password_hash" not in detail.json()["user"]
        assert client.delete(f"/api/users/{target['id']}", headers=headers).status_code == 204


def test_user_assignment_update_revokes_old_department_manager_access(tmp_path):
    app = create_app(
        database_path=tmp_path / "webapp.db",
        token_secret="test-secret-that-is-long-and-local-only",
    )
    with TestClient(app) as client:
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
            "/api/departments", headers=admin_headers, json={"name": "Nhân sự"}
        ).json()
        finance = client.post(
            "/api/departments", headers=admin_headers, json={"name": "Tài chính"}
        ).json()
        manager = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "email": "manager@example.test",
                "display_name": "Manager",
                "password": "ManagerPassphrase123!",
                "role": "manager",
                "department_id": hr["id"],
            },
        ).json()
        login = client.post(
            "/api/login",
            json={
                "email": "manager@example.test",
                "password": "ManagerPassphrase123!",
            },
        )
        manager_headers = _auth(login.json()["access_token"])
        before = client.get("/api/me", headers=manager_headers).json()
        assert before["managed_department_ids"] == [hr["id"]]

        moved = client.patch(
            f"/api/users/{manager['id']}",
            headers=admin_headers,
            json={"role": "member", "department_id": finance["id"]},
        )
        assert moved.status_code == 200, moved.text
        member_profile = client.get("/api/me", headers=manager_headers).json()
        assert member_profile["role"] == "member"
        assert member_profile["department_ids"] == [finance["id"]]
        assert member_profile["managed_department_ids"] == []

        promoted = client.patch(
            f"/api/users/{manager['id']}",
            headers=admin_headers,
            json={"role": "manager"},
        )
        assert promoted.status_code == 200, promoted.text
        manager_profile = client.get("/api/me", headers=manager_headers).json()
        assert manager_profile["managed_department_ids"] == [finance["id"]]
        assert client.post(
            "/api/documents",
            headers=manager_headers,
            json={
                "title": "Sai phòng",
                "content": "Không còn quyền tạo tài liệu cho phòng nhân sự.",
                "access_scope": "department",
                "department_id": hr["id"],
            },
        ).status_code == 403
        assert client.post(
            "/api/documents",
            headers=manager_headers,
            json={
                "title": "Đúng phòng",
                "content": "Quản lý được tạo tài liệu cho phòng tài chính.",
                "access_scope": "department",
                "department_id": finance["id"],
            },
        ).status_code == 201


def test_manager_assignment_requires_department(tmp_path):
    app = create_app(
        database_path=tmp_path / "webapp.db",
        token_secret="test-secret-that-is-long-and-local-only",
    )
    with TestClient(app) as client:
        setup = client.post(
            "/api/setup",
            json={
                "email": "admin@example.test",
                "display_name": "Admin",
                "password": "AdminPassphrase123!",
            },
        )
        headers = _auth(setup.json()["access_token"])
        response = client.post(
            "/api/users",
            headers=headers,
            json={
                "email": "manager@example.test",
                "display_name": "Manager",
                "password": "ManagerPassphrase123!",
                "role": "manager",
                "department_id": None,
            },
        )
        assert response.status_code == 422


class _AssignmentBackend:
    def __init__(self):
        self.profile = {
            "id": "user-1",
            "email": "manager@example.test",
            "display_name": "Manager",
            "role": "manager",
            "department_id": "department-hr",
            "is_active": True,
        }
        self.memberships = [
            {"department_id": "department-hr", "user_id": "user-1", "role": "manager"}
        ]
        self.calls = []

    def initialize(self):
        pass

    def close(self):
        pass

    def user_from_token(self, token):
        assert token == "admin-token"
        return {
            "id": "admin-1",
            "email": "admin@example.test",
            "display_name": "Admin",
            "role": "admin",
            "department_id": None,
            "department_ids": [],
            "managed_department_ids": [],
            "_access_token": token,
        }

    def list_users(self, token):
        return [dict(self.profile)]

    def user_memberships(self, token, user_id):
        return [dict(row) for row in self.memberships]

    def delete_membership(self, token, department_id, user_id):
        self.calls.append(("delete_membership", department_id))
        self.memberships = [
            row
            for row in self.memberships
            if str(row["department_id"]) != str(department_id)
        ]

    def update_membership(self, token, department_id, user_id, role):
        self.calls.append(("update_membership", department_id, role))
        for row in self.memberships:
            if str(row["department_id"]) == str(department_id):
                row["role"] = role

    def add_membership(self, token, department_id, user_id, role):
        self.calls.append(("add_membership", department_id, role))
        self.memberships.append(
            {"department_id": department_id, "user_id": user_id, "role": role}
        )

    def update_user(self, user_id, updates):
        self.calls.append(("update_user", updates.get("department_id"), updates.get("role")))
        self.profile.update(updates)
        return dict(self.profile)

    def audit(self, *args, **kwargs):
        pass


def test_supabase_assignment_revokes_old_membership_before_profile_update(tmp_path):
    backend = _AssignmentBackend()
    app = create_app(
        database_path=tmp_path / "unused.db",
        supabase_backend=backend,
    )
    with TestClient(app) as client:
        response = client.patch(
            "/api/users/user-1",
            headers=_auth("admin-token"),
            json={"role": "member", "department_id": "department-finance"},
        )

    assert response.status_code == 200, response.text
    assert backend.calls == [
        ("delete_membership", "department-hr"),
        ("update_user", "department-finance", "member"),
        ("add_membership", "department-finance", "member"),
    ]
    assert backend.memberships == [
        {
            "department_id": "department-finance",
            "user_id": "user-1",
            "role": "member",
        }
    ]


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
