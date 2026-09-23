"""Phonebook API — FastAPI port of the Node.js/Express backend.

Same routes, same request/response shapes, same SQL Server stored
procedures. Sync endpoints + pyodbc (FastAPI runs them in a threadpool).
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .errors import AppError
from .routers import auth as auth_router
from .routers import contacts as contacts_router
from .services import ContactService

log = logging.getLogger("phonebook")
logging.basicConfig(level=logging.INFO)

ROOT = Path(__file__).resolve().parent.parent.parent  # project root
DIST = ROOT / "client" / "dist"


async def _keepalive(service: ContactService):
    """Ops keepalive (not CRUD): keep pool/plans warm every 25s."""
    while True:
        await asyncio.sleep(25)
        try:
            await asyncio.to_thread(service.get_paged, 1, 1, "")
        except Exception:
            pass  # next tick retries


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_keepalive(ContactService()))
    yield
    task.cancel()


app = FastAPI(title="Phonebook API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.message})


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"message": "Internal server error."})


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "phonebook-api"}


app.include_router(contacts_router.router, prefix="/api/contacts")
app.include_router(auth_router.router, prefix="/api/auth")

# Serve the built Vue SPA when client/dist exists (mirrors Express static).
if DIST.joinpath("index.html").is_file():
    app.mount("/assets", StaticFiles(directory=str(DIST / "assets")), name="assets")

    @app.get("/{path:path}")
    def spa_fallback(path: str):
        candidate = DIST / path
        if path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(DIST / "index.html"))
