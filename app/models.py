from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """What the login accepts.

    ``email`` rather than ``username`` because that is what an address-shaped
    identifier is called nearly everywhere, and a client that has to guess
    between the two gets a 422 rather than a 401 — which is the more useful
    failure, since it says the request was wrong rather than the password.
    """

    email: str = Field(examples=["demo@preman.live"])
    password: str = Field(examples=["PremanDemo123!"])


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120, examples=["Renew the certificate"])
    body: str = Field(default="", max_length=2000)


class Note(BaseModel):
    id: str
    title: str
    body: str
    created_at: str


class NoteList(BaseModel):
    items: list[Note]
    total: int
