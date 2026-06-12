from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RegisterUserCommand:
    username: str
    email: str
    password: str
    full_name: str | None = None


@dataclass
class AuthenticateCommand:
    email: str
    password: str
