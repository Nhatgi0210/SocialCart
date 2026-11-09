"""Argon2id for new seeds; verify bcrypt hashes created by BOOT-01."""
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
import bcrypt

hasher = PasswordHasher()
_dummy_hash = hasher.hash("dummy-user-timing-check")


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password: str, hashed: str | None) -> bool:
    try:
        if hashed and hashed.startswith(("$2a$", "$2b$", "$2y$")):
            # Legacy bcrypt truncates at 72 bytes; preserve verification semantics.
            return bcrypt.checkpw(password.encode()[:72], hashed.encode())
        valid = hasher.verify(hashed or _dummy_hash, password)
        return valid and hashed is not None
    except (VerificationError, InvalidHashError, ValueError):
        return False
