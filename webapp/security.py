"""Small dependency-free password and signed-session helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time


PBKDF2_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("Password must contain at least 10 characters.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


def create_token(user_id: int, secret: str, *, ttl_seconds: int = 28_800) -> str:
    payload = {
        "sub": int(user_id),
        "exp": int(time.time()) + ttl_seconds,
        "nonce": secrets.token_hex(8),
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).rstrip(b"=")
    signature = hmac.new(secret.encode("utf-8"), encoded, hashlib.sha256).digest()
    return "{}.{}".format(
        encoded.decode("ascii"),
        base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii"),
    )


def decode_token(token: str, secret: str) -> int:
    try:
        payload_part, signature_part = token.split(".", 1)
        encoded = payload_part.encode("ascii")
        expected = hmac.new(secret.encode("utf-8"), encoded, hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode(
            signature_part + "=" * (-len(signature_part) % 4)
        )
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("Invalid signature")
        payload = json.loads(
            base64.urlsafe_b64decode(
                payload_part + "=" * (-len(payload_part) % 4)
            )
        )
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("Expired token")
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid or expired session") from exc
