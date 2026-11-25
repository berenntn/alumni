"""Cryptographic security utilities for password hashing and verification.

Uses PBKDF2-HMAC-SHA256 with 100,000 iterations and random salt, adhering to
NIST and OWASP password storage recommendations with zero external dependencies.
"""

import hashlib
import secrets
from typing import Optional


def hash_password(password: str) -> str:
    """Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a unique salt.

    Args:
        password: Plaintext password string to hash.

    Returns:
        Formatted hash string: 'pbkdf2_sha256$<iterations>$<salt>$<hash>'
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = secrets.token_hex(16)
    iterations = 100_000
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${derived_key}"


def verify_password(password: str, hashed_password: Optional[str]) -> bool:
    """Verifies a plaintext password against a stored hash using constant-time comparison.

    Args:
        password: Candidate plaintext password.
        hashed_password: Stored hash string in format 'pbkdf2_sha256$<iterations>$<salt>$<hash>'.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    if not password or not hashed_password:
        return False

    try:
        parts = hashed_password.split("$")
        if len(parts) != 4:
            return False

        algorithm, iterations_str, salt, expected_hash = parts
        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_str)
        computed_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()

        return secrets.compare_digest(computed_hash, expected_hash)
    except Exception:
        return False
