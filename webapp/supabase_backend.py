"""Optional Supabase Auth/PostgREST backend for the web product.

The browser never receives the service-role key. User-scoped operations forward
the validated Supabase access token so Postgres RLS remains the authorization
boundary before retrieval or reranking.
"""

from __future__ import annotations

import os
import hmac
from typing import Any
from urllib.parse import quote

import httpx


class SupabaseBackendError(RuntimeError):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class SupabaseBackend:
    def __init__(
        self,
        url: str,
        anon_key: str,
        *,
        service_role_key: str | None = None,
        bootstrap_token: str | None = None,
        client: httpx.Client | None = None,
    ):
        self.url = url.rstrip("/")
        self.anon_key = anon_key
        self.service_role_key = service_role_key
        self.bootstrap_token = bootstrap_token
        self.client = client or httpx.Client(timeout=15)

    @classmethod
    def from_environment(cls) -> "SupabaseBackend":
        url = os.getenv("SUPABASE_URL", "").strip()
        public_key = (
            os.getenv("SUPABASE_PUBLISHABLE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or ""
        ).strip()
        secret_key = (
            os.getenv("SUPABASE_SECRET_KEY")
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or ""
        ).strip()
        if not url or not public_key:
            raise RuntimeError(
                "WEBAPP_BACKEND=supabase requires SUPABASE_URL and a publishable/anon key"
            )
        return cls(
            url,
            public_key,
            service_role_key=secret_key or None,
            bootstrap_token=os.getenv("SUPABASE_BOOTSTRAP_TOKEN") or None,
        )

    def initialize(self) -> None:
        """Schema is managed by versioned SQL migrations, not app startup."""

    def close(self) -> None:
        self.client.close()

    def health_details(self) -> dict[str, Any]:
        return {
            "auth": "supabase_auth",
            "persistence": "supabase_postgres_rls",
            "admin_api_configured": bool(self.service_role_key),
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        service: bool = False,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> httpx.Response:
        credential = self.service_role_key if service else self.anon_key
        if service and not credential:
            raise SupabaseBackendError(
                503,
                "Supabase admin operation requires a server-side service-role key",
            )
        request_headers = {"apikey": credential or ""}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        elif credential and not credential.startswith("sb_"):
            # Legacy anon/service_role keys are JWTs. New sb_* keys are opaque
            # and must be sent as apikey, not treated as a user JWT.
            request_headers["Authorization"] = f"Bearer {credential}"
        if headers:
            request_headers.update(headers)
        try:
            response = self.client.request(
                method,
                f"{self.url}{path}",
                headers=request_headers,
                **kwargs,
            )
        except httpx.RequestError as exc:
            raise SupabaseBackendError(503, "Supabase is temporarily unavailable") from exc
        if response.is_error:
            try:
                payload = response.json()
                detail = (
                    payload.get("msg")
                    or payload.get("message")
                    or payload.get("error_description")
                    or payload.get("error")
                )
            except ValueError:
                detail = None
            raise SupabaseBackendError(
                response.status_code,
                str(detail or "Supabase request failed"),
            )
        return response

    def setup_status(self) -> dict[str, Any]:
        if not self.service_role_key or not self.bootstrap_token:
            return {"needs_setup": False, "admin_setup_available": False}
        response = self._request(
            "GET",
            "/rest/v1/profiles",
            service=True,
            params={"select": "id", "limit": "1"},
        )
        return {
            "needs_setup": len(response.json()) == 0,
            "admin_setup_available": True,
        }

    def bootstrap_admin(
        self,
        *,
        email: str,
        display_name: str,
        password: str,
        bootstrap_token: str | None,
    ) -> str:
        if (
            not self.bootstrap_token
            or not bootstrap_token
            or not hmac.compare_digest(self.bootstrap_token, bootstrap_token)
        ):
            raise SupabaseBackendError(403, "Supabase HTTP bootstrap is disabled")
        if not self.setup_status()["needs_setup"]:
            raise SupabaseBackendError(409, "Setup already completed")
        auth_response = self._request(
            "POST",
            "/auth/v1/admin/users",
            service=True,
            json={
                "email": email,
                "password": password,
                "email_confirm": True,
            },
        )
        user_id = auth_response.json()["id"]
        try:
            self._request(
                "POST",
                "/rest/v1/rpc/bootstrap_admin_profile",
                service=True,
                json={
                    "target_user_id": user_id,
                    "target_email": email,
                    "target_display_name": display_name,
                },
            )
        except Exception:
            self._delete_auth_user(str(user_id))
            raise
        return self.login(email, password)

    def login(self, email: str, password: str) -> str:
        response = self._request(
            "POST",
            "/auth/v1/token",
            params={"grant_type": "password"},
            json={"email": email, "password": password},
        )
        return str(response.json()["access_token"])

    def user_from_token(self, token: str) -> dict[str, Any]:
        auth_user = self._request("GET", "/auth/v1/user", token=token).json()
        response = self._request(
            "GET",
            "/rest/v1/profiles",
            token=token,
            params={
                "select": "id,email,display_name,role,department_id,is_active,created_at,departments(name)",
                "id": f"eq.{auth_user['id']}",
                "limit": "1",
            },
        )
        rows = response.json()
        if not rows:
            raise SupabaseBackendError(403, "User profile is missing")
        user = rows[0]
        if not user.get("is_active", True):
            raise SupabaseBackendError(401, "User is inactive")
        department = user.pop("departments", None)
        user["department_name"] = department.get("name") if department else None
        memberships = self._request(
            "GET",
            "/rest/v1/department_memberships",
            token=token,
            params={
                "select": "department_id,role",
                "user_id": f"eq.{auth_user['id']}",
            },
        ).json()
        user["department_ids"] = [row["department_id"] for row in memberships]
        if user.get("department_id") and user["department_id"] not in user["department_ids"]:
            user["department_ids"].append(user["department_id"])
        user["managed_department_ids"] = [
            row["department_id"] for row in memberships if row["role"] == "manager"
        ]
        user["_access_token"] = token
        return user

    def list_departments(self, token: str) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            "/rest/v1/departments",
            token=token,
            params={"select": "*", "order": "name"},
        ).json()

    def create_department(self, token: str, name: str, description: str = "") -> dict[str, Any]:
        rows = self._request(
            "POST",
            "/rest/v1/departments",
            token=token,
            headers={"Prefer": "return=representation"},
            json={"name": name, "description": description},
        ).json()
        return rows[0]

    def update_department(self, token: str, department_id: str, name: str, description: str = "") -> dict[str, Any]:
        rows = self._request(
            "PATCH",
            "/rest/v1/departments",
            token=token,
            headers={"Prefer": "return=representation"},
            params={"id": f"eq.{department_id}"},
            json={"name": name, "description": description},
        ).json()
        if not rows:
            raise SupabaseBackendError(404, "Không tìm thấy phòng ban")
        return rows[0]

    def delete_department(self, token: str, department_id: str) -> None:
        self._request(
            "DELETE", "/rest/v1/departments", token=token, params={"id": f"eq.{department_id}"}
        )

    def department_memberships(self, token: str, department_id: str) -> list[dict[str, Any]]:
        members = self._request(
            "GET",
            "/rest/v1/department_memberships",
            token=token,
            params={"select": "department_id,user_id,role,created_at", "department_id": f"eq.{department_id}"},
        ).json()
        if not members:
            return []
        ids = ",".join(str(member["user_id"]) for member in members)
        profiles = self._request(
            "GET", "/rest/v1/profiles", service=True,
            params={"select": "id,display_name,email,is_active", "id": f"in.({ids})"},
        ).json()
        by_id = {str(profile["id"]): profile for profile in profiles}
        for member in members:
            profile = by_id.get(str(member["user_id"]), {})
            member.update({"display_name": profile.get("display_name"), "email": profile.get("email"), "is_active": profile.get("is_active", True)})
        return members

    def add_membership(self, token: str, department_id: str, user_id: str, role: str) -> None:
        self._request(
            "POST",
            "/rest/v1/department_memberships",
            token=token,
            headers={"Prefer": "return=minimal"},
            json={"department_id": department_id, "user_id": user_id, "role": role},
        )

    def update_membership(self, token: str, department_id: str, user_id: str, role: str) -> None:
        self._request(
            "PATCH",
            "/rest/v1/department_memberships",
            token=token,
            params={"department_id": f"eq.{department_id}", "user_id": f"eq.{user_id}"},
            json={"role": role},
        )

    def delete_membership(self, token: str, department_id: str, user_id: str) -> None:
        self._request(
            "DELETE",
            "/rest/v1/department_memberships",
            token=token,
            params={"department_id": f"eq.{department_id}", "user_id": f"eq.{user_id}"},
        )

    def documents_in_department(self, token: str, department_id: str) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            "/rest/v1/documents",
            token=token,
            params={"select": "id", "department_id": f"eq.{department_id}", "limit": "1"},
        ).json()

    def list_users(self, token: str) -> list[dict[str, Any]]:
        rows = self._request(
            "GET",
            "/rest/v1/profiles",
            token=token,
            params={
                "select": "id,email,display_name,role,department_id,is_active,created_at,departments(name)",
                "order": "created_at",
            },
        ).json()
        for row in rows:
            department = row.pop("departments", None)
            row["department_name"] = department.get("name") if department else None
        return rows

    def create_user(
        self,
        *,
        email: str,
        display_name: str,
        password: str,
        role: str,
        department_id: str | int | None,
    ) -> str:
        auth_response = self._request(
            "POST",
            "/auth/v1/admin/users",
            service=True,
            json={
                "email": email,
                "password": password,
                "email_confirm": True,
            },
        )
        user_id = auth_response.json()["id"]
        try:
            self._request(
                "POST",
                "/rest/v1/profiles",
                service=True,
                headers={"Prefer": "return=minimal"},
                json={
                    "id": user_id,
                    "email": email,
                    "display_name": display_name,
                    "role": role,
                    "department_id": department_id,
                },
            )
        except Exception:
            self._delete_auth_user(str(user_id))
            raise
        return str(user_id)

    def update_profile(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        allowed = {"email", "display_name", "role", "department_id", "is_active"}
        payload = {key: value for key, value in updates.items() if key in allowed}
        rows = self._request(
            "PATCH", "/rest/v1/profiles", service=True,
            headers={"Prefer": "return=representation"}, params={"id": f"eq.{user_id}"}, json=payload,
        ).json()
        if not rows:
            raise SupabaseBackendError(404, "Không tìm thấy người dùng")
        return rows[0]

    def update_user(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Admin-only identity update; email must be changed in Auth and profile."""
        updates = dict(updates)
        email = updates.pop("email", None)
        if email:
            self._request(
                "PUT", f"/auth/v1/admin/users/{user_id}", service=True,
                json={"email": email, "email_confirm": True},
            )
            updates["email"] = email
        return self.update_profile(user_id, updates)

    def change_password(self, user_id: str, password: str) -> None:
        self._request("PUT", f"/auth/v1/admin/users/{user_id}", service=True, json={"password": password})

    def delete_user(self, user_id: str) -> None:
        self._request("DELETE", f"/auth/v1/admin/users/{user_id}", service=True)

    def owned_documents(self, user_id: str) -> list[dict[str, Any]]:
        return self._request(
            "GET", "/rest/v1/documents", service=True,
            params={"select": "id", "owner_id": f"eq.{user_id}", "limit": "1"},
        ).json()

    def _delete_auth_user(self, user_id: str) -> None:
        try:
            self._request(
                "DELETE",
                f"/auth/v1/admin/users/{user_id}",
                service=True,
            )
        except SupabaseBackendError:
            # Preserve the original failure. Operators can reconcile from logs.
            pass

    def allowed_documents(self, token: str) -> list[dict[str, Any]]:
        """RLS filters rows in Postgres before the response reaches retrieval."""
        rows = self._request(
            "GET",
            "/rest/v1/documents",
            token=token,
            params={
                "select": "id,title,content,scope,department_id,owner_id,source_name,mime_type,storage_path,processing_status,checksum,created_at,departments(name),document_label_links(document_labels(id,name,color))",
                "order": "created_at",
            },
        ).json()
        for row in rows:
            department = row.pop("departments", None)
            row["department_name"] = department.get("name") if department else None
            row["access_scope"] = row.pop("scope")
            links = row.pop("document_label_links", []) or []
            row["labels"] = [link["document_labels"] for link in links if link.get("document_labels")]
        return rows

    def allowed_document_chunks(self, token: str) -> list[dict[str, Any]]:
        rows = self._request(
            "GET",
            "/rest/v1/document_chunks",
            token=token,
            params={
                "select": "id,document_id,content,locator,chunk_index,documents(id,title,source_name,scope,department_id,departments(name))",
                "order": "document_id,chunk_index",
            },
        ).json()
        normalized: list[dict[str, Any]] = []
        for row in rows:
            document = row.pop("documents", None) or {}
            department = document.pop("departments", None) or {}
            normalized.append(
                {
                    **row,
                    "title": document.get("title", "Tài liệu"),
                    "source_name": document.get("source_name", ""),
                    "access_scope": document.get("scope", "department"),
                    "department_id": document.get("department_id"),
                    "department_name": department.get("name"),
                }
            )
        return normalized

    def document_chunks(self, token: str, document_id: str) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            "/rest/v1/document_chunks",
            token=token,
            params={
                "select": "id,locator,chunk_index,content",
                "document_id": f"eq.{document_id}",
                "order": "chunk_index",
            },
        ).json()

    def create_document(
        self,
        token: str,
        *,
        title: str,
        content: str,
        access_scope: str,
        department_id: str | int | None,
        owner_id: str,
        source_name: str = "",
        mime_type: str = "text/plain",
        storage_path: str = "",
        checksum: str = "",
    ) -> str:
        # The RPC verifies owner, active role, and manager membership inside
        # Postgres.  It avoids a recursive RLS evaluation while keeping the
        # authenticated user as the authorization principal.
        document_id = self._request(
            "POST",
            "/rest/v1/rpc/create_authorized_document",
            token=token,
            json={
                "p_title": title,
                "p_content": content,
                "p_scope": access_scope,
                "p_department_id": department_id,
                "p_owner_id": owner_id,
                "p_source_name": source_name,
                "p_mime_type": mime_type,
                "p_storage_path": storage_path,
                "p_checksum": checksum,
                "p_processing_status": "ready",
            },
        ).json()
        return str(document_id)

    def create_document_chunks(self, document_id: str, chunks: list[dict[str, Any]]) -> None:
        """Only trusted server code creates chunks after parsing an authorized upload."""
        self._request(
            "POST",
            "/rest/v1/document_chunks",
            service=True,
            headers={"Prefer": "return=minimal"},
            json=[{**chunk, "document_id": document_id} for chunk in chunks],
        )

    def upload_document_file(self, storage_path: str, payload: bytes, mime_type: str) -> None:
        self._request(
            "POST",
            f"/storage/v1/object/enterprise-documents/{quote(storage_path, safe='/')}",
            service=True,
            headers={"Content-Type": mime_type, "x-upsert": "false"},
            content=payload,
        )

    def signed_document_url(self, storage_path: str) -> str:
        response = self._request(
            "POST",
            f"/storage/v1/object/sign/enterprise-documents/{quote(storage_path, safe='/')}",
            service=True,
            json={"expiresIn": 60},
        ).json()
        signed = response.get("signedURL") or response.get("signedUrl")
        if not signed:
            raise SupabaseBackendError(503, "Không tạo được liên kết tải tài liệu")
        return f"{self.url}/storage/v1{signed}" if signed.startswith("/") else str(signed)

    def delete_document_file(self, storage_path: str) -> None:
        self._request(
            "DELETE",
            f"/storage/v1/object/enterprise-documents/{quote(storage_path, safe='/')}",
            service=True,
        )

    def delete_document(self, token: str, document_id: str) -> None:
        self._request("DELETE", "/rest/v1/documents", token=token, params={"id": f"eq.{document_id}"})

    def delete_document_as_service(self, document_id: str) -> None:
        """Compensating cleanup for a failed multi-step server upload."""
        self._request(
            "DELETE", "/rest/v1/documents", service=True, params={"id": f"eq.{document_id}"}
        )

    def update_document(
        self, token: str, document_id: str, *, title: str, access_scope: str, department_id: str | int | None
    ) -> dict[str, Any]:
        rows = self._request(
            "PATCH", "/rest/v1/documents", token=token,
            headers={"Prefer": "return=representation"}, params={"id": f"eq.{document_id}"},
            json={"title": title, "scope": access_scope, "department_id": department_id},
        ).json()
        if not rows:
            raise SupabaseBackendError(404, "Không tìm thấy tài liệu")
        return rows[0]

    def labels(self, token: str) -> list[dict[str, Any]]:
        return self._request("GET", "/rest/v1/document_labels", token=token, params={"select": "*", "order": "name"}).json()

    def create_label(self, token: str, name: str, color: str) -> dict[str, Any]:
        rows = self._request(
            "POST", "/rest/v1/document_labels", token=token,
            headers={"Prefer": "return=representation"}, json={"name": name, "color": color},
        ).json()
        return rows[0]

    def replace_document_labels(self, document_id: str, label_ids: list[str]) -> None:
        self._request("DELETE", "/rest/v1/document_label_links", service=True, params={"document_id": f"eq.{document_id}"})
        if label_ids:
            self._request(
                "POST", "/rest/v1/document_label_links", service=True,
                headers={"Prefer": "return=minimal"},
                json=[{"document_id": document_id, "label_id": label_id} for label_id in label_ids],
            )

    def replace_document_grants(self, document_id: str, user_ids: list[str]) -> None:
        self._request("DELETE", "/rest/v1/document_access_grants", service=True, params={"document_id": f"eq.{document_id}"})
        if user_ids:
            self._request(
                "POST", "/rest/v1/document_access_grants", service=True,
                headers={"Prefer": "return=minimal"},
                json=[{"document_id": document_id, "user_id": user_id} for user_id in user_ids],
            )

    def audit(
        self,
        token: str,
        *,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str = "",
        outcome: str,
        detail: str = "",
    ) -> None:
        self._request(
            "POST",
            "/rest/v1/rpc/append_audit_event",
            token=token,
            json={
                "event_action": action,
                "event_resource_type": resource_type,
                "event_resource_id": resource_id or None,
                "event_outcome": outcome,
                "event_detail": detail[:500],
            },
        )

    def audit_logs(self, token: str) -> list[dict[str, Any]]:
        rows = self._request(
            "GET",
            "/rest/v1/audit_logs",
            token=token,
            params={"select": "*", "order": "created_at.desc", "limit": "200"},
        ).json()
        for row in rows:
            metadata = row.pop("metadata", {}) or {}
            row["user_id"] = row.get("actor_id")
            row["email"] = None
            row["outcome"] = metadata.get("outcome", "")
            row["detail"] = metadata.get("detail", "")
        return rows
