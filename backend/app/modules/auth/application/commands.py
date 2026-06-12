from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RegisterUserCommand:
    username: str
    password: str
    email: str | None = None
    full_name: str | None = None


@dataclass
class AuthenticateCommand:
    username: str
    password: str
