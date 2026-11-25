#!/usr/bin/env python3
"""Admin account bootstrap utility for Alumni Tracking System.

Usage:
    ./venv/bin/python scripts/bootstrap_admin.py [--email berentn05@gmail.com]

Requirements:
1. Verify that this email already exists in the PostgreSQL database.
2. Do not create a duplicate account.
3. Promote this existing user to role "admin".
4. Do not modify their password or other personal information.
5. Create a secure, repeatable admin bootstrap command/script.
6. The bootstrap operation must be safe to run more than once (idempotent).
7. If the account does not exist, report this clearly and do not create an account automatically.
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.services.admin_service import AdminService

DEFAULT_ADMIN_EMAIL = "berentn05@gmail.com"


def bootstrap_admin(email: str = DEFAULT_ADMIN_EMAIL) -> int:
    """Promotes existing registered user to admin role safely and idempotently.

    Returns:
        0 on success (promoted or already admin), 1 on user not found or error.
    """
    print(f"[BOOTSTRAP] Checking status for target admin account: '{email}'...")
    result = AdminService.promote_user_to_admin(email)
    status = result.get("status")
    message = result.get("message")

    if status == "promoted":
        print(f"[SUCCESS] {message}")
        print(f"[INFO] User ID: {result['user']['id']}, Role: {result['user']['role']}")
        return 0
    elif status == "already_admin":
        print(f"[INFO] {message}")
        print(f"[INFO] User ID: {result['user']['id']}, Role: {result['user']['role']}")
        return 0
    elif status == "not_found":
        print(f"[ERROR] {message}")
        print(
            "[ACTION REQUIRED] Please have the user register their account first via the Web Register page (/register) "
            "or API (/api/register) before running this promotion script."
        )
        return 1
    else:
        print(f"[ERROR] Unexpected status '{status}': {message}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap or promote an existing user account to System Administrator."
    )
    parser.add_argument(
        "--email",
        default=DEFAULT_ADMIN_EMAIL,
        help=f"Target user email address (default: {DEFAULT_ADMIN_EMAIL})",
    )
    args = parser.parse_args()

    exit_code = bootstrap_admin(args.email)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
