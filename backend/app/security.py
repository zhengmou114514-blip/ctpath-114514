from __future__ import annotations

import hashlib
import hmac
import secrets


PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 390000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${digest}"


def is_hashed_password(value: str) -> bool:
    return value.startswith(f"{PASSWORD_SCHEME}$")


def verify_password(password: str, stored_value: str) -> bool:
    if not stored_value:
        return False
    if not is_hashed_password(stored_value):
        return hmac.compare_digest(stored_value, password)

    try:
        scheme, iterations, salt, digest = stored_value.split("$", 3)
    except ValueError:
        return False
    if scheme != PASSWORD_SCHEME:
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        int(iterations),
    ).hex()
    return hmac.compare_digest(derived, digest)
