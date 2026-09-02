"""A notes service that will not talk to you until you log in.

Seven routes. The two in ``public.py`` answer to anyone; the five here answer
401 without a token. That ratio is the point — it is the shape of nearly every
real backend, and the shape that makes an API testing tool useless until it can
authenticate.

Deliberately small. The whole thing fits in one reading, so when a run against
it does something surprising, this is not where the surprise came from.
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Response, status

from app import store
from app.auth import require_auth
from app.models import Note, NoteCreate, NoteList
from app.public_routes import router as public_router

app = FastAPI(
    title="Notes Service",
    version="1.0.0",
    description="A small authenticated notes API, used to exercise PreMan end to end.",
)

app.include_router(public_router)

store.seed()


@app.get("/me", tags=["auth"])
def me(email: str = Depends(require_auth)) -> dict[str, str]:
    """Who the token belongs to. The cheapest way to check one still works."""
    return {"email": email}


@app.get("/notes", response_model=NoteList, tags=["notes"])
def list_notes(email: str = Depends(require_auth)) -> NoteList:
    items = store.listing()
    return NoteList(items=items, total=len(items))


@app.get("/notes/{note_id}", response_model=Note, tags=["notes"])
def get_note(note_id: str, email: str = Depends(require_auth)) -> Note:
    """404 for a note that is not here — but only once the caller is known.

    The order matters and is easy to get wrong. Authenticating first means an
    anonymous caller cannot use the difference between 404 and 200 to find out
    which note ids exist.
    """
    note = store.get(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="note not found")
    return note


@app.post(
    "/notes",
    response_model=Note,
    status_code=status.HTTP_201_CREATED,
    tags=["notes"],
)
def create_note(payload: NoteCreate, email: str = Depends(require_auth)) -> Note:
    """Paired with the delete below, so a create can always be undone."""
    return store.create(payload)


@app.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["notes"],
)
def delete_note(note_id: str, email: str = Depends(require_auth)) -> Response:
    if not store.delete(note_id):
        raise HTTPException(status_code=404, detail="note not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Lambda entry point. Imported defensively so the module still loads — and the
# app still runs under plain uvicorn — on a machine with no mangum installed.
try:  # pragma: no cover - deployment glue
    from mangum import Mangum

    handler = Mangum(app)
except ImportError:  # pragma: no cover - local and sandbox runs take this path
    handler = None
