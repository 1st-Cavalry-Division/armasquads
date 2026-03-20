import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.responses import PlainTextResponse

from .config import Settings
from .squad_xml import SQUAD_DTD, generate_squad_xml
from .sync import perform_sync, sync_loop, sync_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

settings = Settings()

STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Perform an initial sync before accepting traffic
    await perform_sync(settings)
    # Start the background periodic sync
    task = asyncio.create_task(sync_loop(settings))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="ArmA Squads",
    description="Serves squad.xml for Arma 3 from PERSCOM roster data.",
    version="2.0.0",
    lifespan=lifespan,
    # Disable default Swagger UI — this is an internal microservice
    docs_url=None,
    redoc_url=None,
)


@app.get("/squad.xml")
async def serve_squad_xml() -> Response:
    """
    Serves the squad.xml file consumed by Arma 3 clients.
    Configure your in-game squad URL to point here.
    """
    if sync_state.squad_data is None:
        raise HTTPException(
            status_code=503,
            detail="Squad data not yet available — initial sync may still be running.",
        )
    xml = generate_squad_xml(sync_state.squad_data)
    return Response(content=xml, media_type="application/xml")


@app.get("/squad.dtd")
async def serve_squad_dtd() -> Response:
    """Serves the Arma 3 squad DTD referenced by squad.xml."""
    return Response(content=SQUAD_DTD, media_type="application/xml")


@app.get("/{filename}.paa")
async def serve_logo(filename: str) -> Response:
    """
    Serves a PAA logo file from the static/ directory.
    The filename (without extension) is set via LOGO_FILENAME env var.
    """
    # Prevent path traversal — only allow plain filenames with no separators
    if os.sep in filename or "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    logo_path = STATIC_DIR / f"{filename}.paa"

    if not logo_path.exists() or not logo_path.is_file():
        raise HTTPException(status_code=404, detail="Logo file not found.")

    return Response(
        content=logo_path.read_bytes(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}.paa"'},
    )


@app.get("/health")
async def health() -> dict:
    """Health / readiness check. Returns last sync time and member count."""
    return {
        "status": "ok" if sync_state.squad_data is not None else "starting",
        "last_sync": sync_state.last_sync.isoformat() if sync_state.last_sync else None,
        "last_error": sync_state.last_error,
        "member_count": (
            len(sync_state.squad_data.members) if sync_state.squad_data else 0
        ),
    }


@app.post("/sync")
async def trigger_sync(x_sync_key: str = Header(..., alias="X-Sync-Key")) -> dict:
    """
    Manually trigger an out-of-band PERSCOM sync.
    Requires the X-Sync-Key header to match the SYNC_KEY env var.
    """
    if x_sync_key != settings.sync_key:
        raise HTTPException(status_code=403, detail="Invalid sync key.")
    # Fire-and-forget — don't block the response
    asyncio.create_task(perform_sync(settings))
    return {"status": "sync triggered"}
