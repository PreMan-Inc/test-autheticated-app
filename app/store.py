"""Notes, in memory, per process.

State resets when the process does. That is fine for what this is: a subject to
test against, not a service anyone depends on. It also means every deploy starts
from the same three seeded notes, so a run against it is repeatable.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.models import Note, NoteCreate

_NOTES: dict[str, Note] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def seed() -> None:
    if _NOTES:
        return
    for title, body in (
        ("Renew the staging certificate", "Expires at the end of the month."),
        ("Write the incident review", "Include the timeline and the rollback."),
        ("Delete the old feature flag", "Nothing has read it since April."),
    ):
        create(NoteCreate(title=title, body=body))


def create(payload: NoteCreate) -> Note:
    note = Note(
        id=str(uuid.uuid4()),
        title=payload.title,
        body=payload.body,
        created_at=_now(),
    )
    _NOTES[note.id] = note
    return note


def get(note_id: str) -> Note | None:
    return _NOTES.get(note_id)


def listing() -> list[Note]:
    """Newest first, which is the order anyone reading a note list wants."""
    return sorted(_NOTES.values(), key=lambda note: note.created_at, reverse=True)


def delete(note_id: str) -> bool:
    return _NOTES.pop(note_id, None) is not None
