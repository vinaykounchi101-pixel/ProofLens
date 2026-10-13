"""Cryptographic security utilities (password hashing and token verification)."""

import hashlib
import hmac
import os
import secrets


def hash_password(password: str) -> str:
    """Hashes password with random salt using standard library PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored salt$hash string."""
    try:
        salt, key_hex = hashed_password.split("$", 1)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100_000,
        )
        return hmac.compare_digest(actual_key, expected_key)
    except Exception:
        return False
