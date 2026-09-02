"""One test account, one token, and a dependency that refuses without it.

Stdlib only. A demo API that pulled in a JWT library would spend its first
paragraph explaining the library rather than the thing being demonstrated, and
the point here is the shape of the exchange, not the cryptography: a signed,
expiring bearer token, checked on every protected route.

The token is deliberately short-lived. Fifteen minutes is realistic for an
access token, and it is also short enough to watch a long test run outlive one —
which is the interesting case, because that is when re-authentication has to
happen for the run to stay honest about whose fault a 401 is.
"""

from __future__ import annotations

import base64
import hmac
import json
import os
import time
from hashlib import sha256

from fastapi import Header, HTTPException, status

# A demo secret in the source on purpose: this service holds nothing, and a
# stable value keeps a token working across a cold start. Override it in a
# deployment and every previously issued token stops verifying, which is the
# behaviour you want from a signing key.
SECRET = os.getenv("AUTH_SECRET", "demo-signing-key-not-a-real-secret")

DEMO_EMAIL = os.getenv("DEMO_EMAIL", "demo@preman.live")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "PremanDemo123!")

TOKEN_TTL_SECONDS = int(os.getenv("TOKEN_TTL_SECONDS", "900"))


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def issue_token(email: str) -> tuple[str, int]:
    """A signed ``payload.signature`` pair, and how long it is good for."""
    payload = {"sub": email, "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64(hmac.new(SECRET.encode(), body.encode(), sha256).digest())
    return f"{body}.{signature}", TOKEN_TTL_SECONDS


def read_token(token: str) -> str:
    """The email the token was issued to, or a 401 saying which part failed.

    Expired and forged are answered differently because they are different
    problems: one means log in again, the other means something is wrong with
    the caller. Both are 401, so the distinction lives in the message.
    """
    try:
        body, signature = token.split(".", 1)
        expected = _b64(hmac.new(SECRET.encode(), body.encode(), sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("bad signature")
        payload = json.loads(_unb64(body))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="that token is not one this service issued",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="that token has expired; log in again",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return str(payload.get("sub") or "")


def require_auth(authorization: str = Header(default="")) -> str:
    """Every protected route depends on this. No header, no answer.

    Named ``require_auth`` rather than ``current_user`` because the name is read
    by more than a person: a scanner deciding whether a route is protected has
    the source and nothing else, and a dependency called ``get_user`` is
    indistinguishable from one that loads a public profile.
    """
    scheme, _, token = str(authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="this endpoint needs a bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return read_token(token.strip())
