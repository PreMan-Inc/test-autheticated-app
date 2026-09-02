"""The two routes that answer without a credential.

They live apart from the rest deliberately. Everything in this file is public
and everything in ``main.py`` is not, so which of the two a route is written in
is itself the answer — no reader, and no tool reading the source, has to work it
out from the signature.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.auth import DEMO_EMAIL, DEMO_PASSWORD, issue_token
from app.models import LoginRequest, LoginResponse

router = APIRouter()


@router.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    """Public, and it has to be.

    Something has to answer before a credential exists — a load balancer, a
    deploy check, or a tool working out whether the address it was given is
    this service at all. A health check behind the login is one nobody can use.
    """
    return {"status": "ok", "service": "notes"}


@router.post("/auth/login", response_model=LoginResponse, tags=["auth"])
def login(payload: LoginRequest) -> LoginResponse:
    """The one route that turns a password into a credential.

    One account, checked against the configured demo pair. A wrong password is
    401 rather than 404 or 422: the request was well formed and the answer is
    no. Which of the two fields was wrong goes unsaid, because saying is how
    you help somebody guess the other one.
    """
    if payload.email != DEMO_EMAIL or payload.password != DEMO_PASSWORD:
        raise HTTPException(status_code=401, detail="email or password is incorrect")
    credential, expires_in = issue_token(payload.email)
    return LoginResponse(access_token=credential, expires_in=expires_in)
