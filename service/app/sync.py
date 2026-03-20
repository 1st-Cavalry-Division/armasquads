import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from .config import Settings
from .models import SquadData
from .perscom_client import PerscomClient
from .squad_xml import personnel_to_member

logger = logging.getLogger(__name__)


class SyncState:
    """Thread-safe holder for the latest synced SquadData."""

    def __init__(self) -> None:
        self.squad_data: Optional[SquadData] = None
        self.last_sync: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self._lock = asyncio.Lock()


# Module-level singleton — imported by main.py and the routes
sync_state = SyncState()


async def perform_sync(settings: Settings) -> None:
    """Pull roster from PERSCOM, build SquadData, and update sync_state."""
    client = PerscomClient(settings)

    status_ids = [
        int(s.strip())
        for s in settings.active_status_ids.split(",")
        if s.strip()
    ]
    unit_ids = (
        [int(u.strip()) for u in settings.filter_unit_ids.split(",") if u.strip()]
        or None
    )

    try:
        logger.info("Starting PERSCOM sync…")
        personnel = await client.get_active_personnel(status_ids, unit_ids)

        members = [personnel_to_member(p) for p in personnel]

        # Sort highest rank first (largest rankOrder = most senior)
        rank_order_map = {
            p.steamId64: (p.rank.rankOrder if p.rank and p.rank.rankOrder else 0)
            for p in personnel
        }
        members.sort(key=lambda m: -rank_order_map.get(m.steam_id, 0))

        new_data = SquadData(
            tag=settings.squad_tag,
            name=settings.squad_name,
            email=settings.squad_email,
            web=settings.squad_web,
            title=settings.squad_title,
            logo=settings.logo_filename,
            members=members,
            last_sync=datetime.now(timezone.utc),
        )

        async with sync_state._lock:
            sync_state.squad_data = new_data
            sync_state.last_sync = new_data.last_sync
            sync_state.last_error = None

        logger.info("Sync complete: %d active members with Steam IDs", len(members))

    except Exception as exc:
        error_msg = str(exc)
        logger.error("Sync failed: %s", error_msg)
        async with sync_state._lock:
            sync_state.last_error = error_msg
        # Don't re-raise — keep any previously cached data available


async def sync_loop(settings: Settings) -> None:
    """Background loop that re-syncs every settings.sync_interval seconds."""
    while True:
        await asyncio.sleep(settings.sync_interval)
        await perform_sync(settings)
