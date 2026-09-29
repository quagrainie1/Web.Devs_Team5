"""
api/auth.py

Task 3: Authentication & Security
----------------------------------
Implements HTTP Basic Authentication for the MoMo Transactions API.

Basic Auth works like this:
  1. The client sends a header: Authorization: Basic <base64(username:password)>
  2. The server decodes it and checks the credentials against a known list.
  3. If missing or wrong, the server responds 401 Unauthorized with a
     WWW-Authenticate header, which is what makes browsers/Postman show a
     login prompt.

Credentials are intentionally simple/hardcoded here for a class assignment.
In a real system these would never live in source code — see the "Why Basic
Auth is weak" section of docs/api_docs.md for the reasoning and stronger
alternatives (JWT, OAuth2).
"""

import base64
VALID_USERS = {
    "admin": "momo2026",
    "teamlead": "webdevs5",
}


def parse_basic_auth_header(header_value: str | None) -> tuple[str, str] | None:
    """
    Parse an 'Authorization: Basic <token>' header value.
    Returns (username, password) on success, or None if the header is
    missing, malformed, or not base64-decodable.
    """
    if not header_value or not header_value.startswith("Basic "):
        return None

    encoded = header_value[len("Basic "):].strip()
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
    except Exception:
        return None

    if ":" not in decoded:
        return None

    username, _, password = decoded.partition(":")
    return username, password


def is_authenticated(header_value: str | None) -> bool:
    """Return True if the Authorization header carries valid credentials."""
    credentials = parse_basic_auth_header(header_value)
    if credentials is None:
        return False

    username, password = credentials
    return VALID_USERS.get(username) == password
