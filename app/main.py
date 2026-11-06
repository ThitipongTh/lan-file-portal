"""AIMsLab File Sharing — FastAPI application.

Serves the public browse/download UI, the admin UI, and the JSON APIs. Downloads
and uploads stream through this process so every byte is metered live. The Share
is the folder mounted at ``config.SHARE_ROOT``; the public can read it, the admin
can manage it.
"""
import asyncio
import hmac
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import Body, Depends, FastAPI, HTTPException, Request, Response, WebSocket
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.websockets import WebSocketDisconnect

from . import config, security
from .metrics import Metrics

metrics = Metrics()
STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def sampler():
        while True:
            await asyncio.sleep(1)
            metrics.sample()

    task = asyncio.create_task(sampler())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title=config.SITE_NAME, lifespan=lifespan, docs_url=None, redoc_url=None)


# --- auth -------------------------------------------------------------------

def require_admin(request: Request) -> None:
    if not config.ADMIN_ENABLED:
        raise HTTPException(status_code=404, detail="admin is disabled")
    if not security.verify_session(request.cookies.get("session", "")):
        raise HTTPException(status_code=401, detail="authentication required")


def _resolve(path: str) -> Path:
    try:
        return security.resolve(path)
    except security.PathError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _name(name: str) -> str:
    try:
        return security.safe_name(name)
    except security.PathError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# --- pages ------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/admin", include_in_schema=False)
def admin_page() -> FileResponse:
    return FileResponse(STATIC / "admin.html")


# --- public API -------------------------------------------------------------

@app.get("/api/list")
def list_dir(path: str = ""):
    target = _resolve(path)
    if not target.is_dir():
        raise HTTPException(status_code=404, detail="folder not found")
    items = []
    for entry in target.iterdir():
        if entry.name.startswith("."):
            continue
        try:
            st = entry.stat()
            is_dir = entry.is_dir()
        except OSError:
            continue
        items.append({
            "name": entry.name,
            "type": "directory" if is_dir else "file",
            "size": None if is_dir else st.st_size,
            "mtime": int(st.st_mtime),
        })
    items.sort(key=lambda i: (i["type"] != "directory", i["name"].lower()))
    return items


@app.get("/download")
def download(path: str):
    target = _resolve(path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    size = target.stat().st_size
    tid = metrics.start_transfer(target.name, "down", size)

    def stream():
        try:
            with open(target, "rb") as f:
                while True:
                    chunk = f.read(config.CHUNK_BYTES)
                    if not chunk:
                        break
                    metrics.add_bytes(tid, len(chunk), "down")
                    yield chunk
        finally:
            metrics.end_transfer(tid)

    ascii_name = target.name.encode("ascii", "replace").decode("ascii").replace('"', "")
    disposition = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(target.name)}"
    headers = {
        "Content-Disposition": disposition,
        "Content-Length": str(size),
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store",
    }
    return StreamingResponse(stream(), media_type="application/octet-stream", headers=headers)


# --- admin: session ---------------------------------------------------------

@app.get("/admin/api/session")
def session_info(request: Request):
    authed = config.ADMIN_ENABLED and security.verify_session(request.cookies.get("session", ""))
    return {"admin_enabled": config.ADMIN_ENABLED, "authenticated": authed}


@app.post("/admin/api/login")
def login(response: Response, password: str = Body(..., embed=True)):
    if not config.ADMIN_ENABLED:
        raise HTTPException(status_code=404, detail="admin is disabled")
    if not hmac.compare_digest(password, config.ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="invalid password")
    response.set_cookie(
        "session", security.make_session(),
        max_age=config.SESSION_TTL_SECONDS, httponly=True, samesite="lax",
    )
    return {"ok": True}


@app.post("/admin/api/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"ok": True}


# --- admin: manage ----------------------------------------------------------

@app.post("/admin/api/mkdir")
def mkdir(path: str = Body("", embed=True), name: str = Body(..., embed=True),
          _: None = Depends(require_admin)):
    folder = _resolve(path)
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail="parent folder not found")
    target = folder / _name(name)
    if target.exists():
        raise HTTPException(status_code=409, detail="a file or folder with that name already exists")
    target.mkdir()
    return {"ok": True}


@app.post("/admin/api/rename")
def rename(path: str = Body("", embed=True), name: str = Body(..., embed=True),
           new_name: str = Body(..., embed=True), _: None = Depends(require_admin)):
    folder = _resolve(path)
    src = security.ensure_within((folder / _name(name)))
    dest = folder / _name(new_name)
    if not src.exists():
        raise HTTPException(status_code=404, detail="item not found")
    if dest.exists():
        raise HTTPException(status_code=409, detail="a file or folder with that name already exists")
    src.rename(dest)
    return {"ok": True}


@app.post("/admin/api/delete")
def delete(path: str = Body("", embed=True), name: str = Body(..., embed=True),
           _: None = Depends(require_admin)):
    folder = _resolve(path)
    target = security.ensure_within((folder / _name(name)))
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()
    else:
        raise HTTPException(status_code=404, detail="item not found")
    return {"ok": True}


@app.put("/admin/api/upload")
async def upload(request: Request, path: str = "", name: str = "",
                 _: None = Depends(require_admin)):
    folder = _resolve(path)
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail="destination folder not found")
    safe = _name(name)
    dest = folder / safe
    if dest.exists():
        raise HTTPException(status_code=409, detail="a file or folder with that name already exists")

    declared = int(request.headers.get("content-length") or 0)
    if config.MAX_UPLOAD_BYTES and declared > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="file exceeds the maximum upload size")

    tmp = folder / f".{safe}.uploading"  # hidden => not listed while in flight
    tid = metrics.start_transfer(safe, "up", declared)
    written = 0
    try:
        with open(tmp, "wb") as f:
            async for chunk in request.stream():
                written += len(chunk)
                if config.MAX_UPLOAD_BYTES and written > config.MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="file exceeds the maximum upload size")
                f.write(chunk)
                metrics.add_bytes(tid, len(chunk), "up")
        tmp.rename(dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    finally:
        metrics.end_transfer(tid)
    return {"ok": True, "name": safe, "bytes": written}


# --- admin: live metrics ----------------------------------------------------

@app.websocket("/admin/ws/metrics")
async def metrics_ws(ws: WebSocket):
    if not config.ADMIN_ENABLED or not security.verify_session(ws.cookies.get("session", "")):
        await ws.close(code=1008)
        return
    await ws.accept()
    try:
        while True:
            await ws.send_json(metrics.snapshot())
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
