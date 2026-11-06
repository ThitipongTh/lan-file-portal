"""Runtime configuration, read once from the environment at import time.

Everything an operator can tune lives here. The Share root is fixed inside
the container (`/srv/shared`); the operator chooses the *host* folder mounted
there via SHARE_PATH in compose.
"""
import os
import secrets
from pathlib import Path

SITE_NAME = "AIMsLab File Sharing"

# The container-side mount point of the Share. The host folder is chosen by the
# operator through SHARE_PATH in compose.yaml and mounted here.
SHARE_ROOT = Path(os.environ.get("SHARE_ROOT", "/srv/shared")).resolve()

# Admin password. Blank => the admin page and all management APIs are disabled;
# public download still works.
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "").strip()
ADMIN_ENABLED = bool(ADMIN_PASSWORD)

# Secret used to sign session cookies. If unset we generate an ephemeral one so
# the app still runs with zero config; the trade-off is that a restart logs the
# admin out. Set SESSION_SECRET in .env to keep sessions across restarts.
SESSION_SECRET = os.environ.get("SESSION_SECRET", "").strip() or secrets.token_urlsafe(32)
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", str(12 * 3600)))

# Upload size cap in bytes (default 2 GiB). 0 disables the cap.
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", str(2 * 1024 ** 3)))

# Streaming chunk size for metered transfers.
CHUNK_BYTES = 256 * 1024
