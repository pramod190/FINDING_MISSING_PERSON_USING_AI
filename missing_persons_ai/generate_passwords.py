"""
Run this script once to generate bcrypt-hashed passwords
and paste them into login_config.yml.

Usage:
    python generate_passwords.py
"""

import bcrypt

passwords = {
    "Admin@123": "Admin password",
    "Officer@456": "Officer password",
    "User@789": "User password",
}

print("Copy these hashed passwords into login_config.yml:\n")
for pw, label in passwords.items():
    hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12)).decode()
    print(f"# {label} — plain: {pw}")
    print(f"password: '{hashed}'\n")
