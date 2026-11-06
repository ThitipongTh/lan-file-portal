"""Path safety and admin session tokens.

Two jobs, both security boundaries:

1. Resolve a caller-supplied relative path against the Share root and refuse
   anything that escapes it (``..``, absolute paths, or symlinks pointing out).
2. Mint and verify signed, expiring session tokens for the admin cookie.
"""
import base64
import hashlib
import hmac
import json
import time
from pathlib import Path

from . import config


class PathError(ValueError):
    """A caller-supplied path or name was unsafe or invalid."""


def _has_dot_component(rel: str) -> bool:
    return any(part.startswith(".") for part in Path(rel).parts)


def ensure_within(target: Path) -> Path:
    """Raise unless ``target`` (already resolved) is the root or inside it."""
    if target != config.SHARE_ROOT and config.SHARE_ROOT not in target.parents:
        raise PathError("path escapes the share root")
    return target


def resolve(rel: str) -> Path:
    """Resolve a relative path within the Share, rejecting escapes and dot-parts.

    ``rel`` uses forward slashes, relative to the Share root. Symlinks are
    resolved, so a link pointing outside the Share is caught by the containment
    check. Dot-prefixed components are rejected (hidden files are not served).
    """
    rel = (rel or "").strip().replace("\\", "/").lstrip("/")
    if _has_dot_component(rel):
        raise PathError("dot-prefixed path components are not allowed")
    target = (config.SHARE_ROOT / rel).resolve()
    return ensure_within(target)


def safe_name(name: str) -> str:
    """Validate a single path segment (a file or folder name, no separators)."""
    name = (name or "").strip()
    if not name or "/" in name or "\\" in name or name in (".", "..") or name.startswith("."):
        raise PathError("invalid name")
    return name


# --- session tokens ---------------------------------------------------------

def _sign(raw: bytes) -> str:
    sig = hmac.new(config.SESSION_SECRET.encode(), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).rstrip(b"=").decode()


def make_session() -> str:
    payload = {"exp": int(time.time()) + config.SESSION_TTL_SECONDS}
    raw = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=")
    return raw.decode() + "." + _sign(raw)


def verify_session(token: str) -> bool:
    try:
        raw, sig = (token or "").split(".", 1)
        if not hmac.compare_digest(_sign(raw.encode()), sig):
            return False
        payload = json.loads(base64.urlsafe_b64decode(raw + "==="))
        return int(payload.get("exp", 0)) > time.time()
    except Exception:
        return False
