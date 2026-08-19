"""Project API key lifecycle (T201) — feature 003 Phase 1.

Constitution Principle II: only a SHA-256 hash and a short, non-secret
prefix are ever persisted. The plaintext key is returned exactly once, at
creation time, and cannot be recovered afterwards. SHA-256 (not bcrypt) is
used deliberately: the key itself is already a long, high-entropy random
token, so a fast deterministic hash is sufficient and — unlike bcrypt —
allows verification without re-deriving from a stored salt per row.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.api_key import ApiKey

_KEY_PREFIX = "llk_"
_PREFIX_DISPLAY_LEN = 12


def _hash_key(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CreatedApiKey:
    """The one and only time the plaintext key is available."""

    api_key: ApiKey
    plaintext: str


def generate_api_key(db: Session, project_id: uuid.UUID, name: str) -> CreatedApiKey:
    plaintext = _KEY_PREFIX + secrets.token_urlsafe(32)
    api_key = ApiKey(
        key_hash=_hash_key(plaintext),
        key_prefix=plaintext[:_PREFIX_DISPLAY_LEN],
        name=name,
        project_id=project_id,
        enabled=True,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return CreatedApiKey(api_key=api_key, plaintext=plaintext)


def list_api_keys(db: Session, project_id: uuid.UUID) -> list[ApiKey]:
    return list(
        db.execute(
            select(ApiKey).where(ApiKey.project_id == project_id).order_by(ApiKey.created_at)
        )
        .scalars()
        .all()
    )


def revoke_api_key(db: Session, key_id: uuid.UUID) -> bool:
    api_key = db.get(ApiKey, key_id)
    if api_key is None:
        return False
    api_key.enabled = False
    db.commit()
    return True


def verify_api_key(db: Session, plaintext: str) -> uuid.UUID | None:
    """Return the owning `project_id` for a valid, enabled key — else `None`.

    Also stamps `last_used_at` so key usage is observable (revocation
    candidates, staleness). Callers MUST treat `None` as "reject" (FR-218)
    regardless of whether the key was invalid, unknown, or disabled.
    """

    api_key = db.execute(
        select(ApiKey).where(ApiKey.key_hash == _hash_key(plaintext))
    ).scalar_one_or_none()
    if api_key is None or not api_key.enabled or api_key.project_id is None:
        return None
    api_key.last_used_at = datetime.now(UTC)
    db.commit()
    return api_key.project_id
