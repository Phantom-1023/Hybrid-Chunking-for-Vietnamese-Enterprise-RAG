"""Optional Supabase Auth/PostgREST backend for the web product.

The browser never receives the service-role key. User-scoped operations forward
the validated Supabase access token so Postgres RLS remains the authorization
boundary before retrieval or reranking.
"""

from __future__ import annotations

import os
import hmac
from typing import Any

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
        user["_access_token"] = token
        return user

    def list_departments(self, token: str) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            "/rest/v1/departments",
            token=token,
            params={"select": "*", "order": "name"},
        ).json()

    def create_department(self, token: str, name: str) -> dict[str, Any]:
        rows = self._request(
            "POST",
            "/rest/v1/departments",
            token=token,
            headers={"Prefer": "return=representation"},
            json={"name": name},
        ).json()
        return rows[0]

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
                "select": "id,title,content,scope,department_id,owner_id,created_at,departments(name)",
                "order": "created_at",
            },
        ).json()
        for row in rows:
            department = row.pop("departments", None)
            row["department_name"] = department.get("name") if department else None
            row["access_scope"] = row.pop("scope")
        return rows

    def create_document(
        self,
        token: str,
        *,
        title: str,
        content: str,
        access_scope: str,
        department_id: str | int | None,
        owner_id: str,
    ) -> str:
        rows = self._request(
            "POST",
            "/rest/v1/documents",
            token=token,
            headers={"Prefer": "return=representation"},
            json={
                "title": title,
                "content": content,
                "scope": access_scope,
                "department_id": department_id,
                "owner_id": owner_id,
            },
        ).json()
        return str(rows[0]["id"])

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
