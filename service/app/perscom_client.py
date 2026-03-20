import logging
import re
from typing import List, Optional

import httpx

from .config import Settings
from .models import PerscomPersonnel

logger = logging.getLogger(__name__)

_PAGE_SIZE = 100

# Steam ID 64: exactly 17 digits, always starts with 7656119
_STEAM_ID_RE = re.compile(r"^7656119\d{10}$")


def is_valid_steam_id64(value: str) -> bool:
    """Return True only if value is a well-formed Steam ID 64."""
    return bool(value and _STEAM_ID_RE.match(value))


class PerscomClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.perscom_api_url.rstrip("/")
        self._headers = {
            "X-API-Key": settings.perscom_api_key,
            "Accept": "application/json",
        }

    async def get_active_personnel(
        self,
        status_ids: List[int],
        unit_ids: Optional[List[int]] = None,
    ) -> List[PerscomPersonnel]:
        """
        Fetch all personnel from PERSCOM and return only those matching
        the given status IDs (and optionally unit IDs) who have a steamId64.
        Handles pagination automatically.
        """
        results: List[PerscomPersonnel] = []
        offset = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params: dict = {
                    "includeRelations": "true",
                    "limit": _PAGE_SIZE,
                    "offset": offset,
                    "sortBy": "rank",
                    "sortDirection": "asc",
                }

                response = await client.get(
                    f"{self._base_url}/api/perscom/personnel",
                    headers=self._headers,
                    params=params,
                )
                response.raise_for_status()
                body = response.json()

                if not body.get("success"):
                    raise ValueError(f"PERSCOM API returned failure: {body}")

                data = body.get("data", {})
                # The list endpoint wraps results: {"data": {"personnel": [...], "total": N}}
                if isinstance(data, dict):
                    batch: list = data.get("personnel", [])
                    total: int = data.get("total", 0)
                else:
                    # Fallback: older/flat array response
                    batch = data if isinstance(data, list) else []
                    total = len(batch)

                if not batch:
                    break

                for raw in batch:
                    try:
                        person = PerscomPersonnel.model_validate(raw)
                    except Exception as exc:
                        logger.warning(
                            "Skipping unparseable personnel record "
                            "(perscomId=%s): %s",
                            raw.get("perscomId"),
                            exc,
                        )
                        continue

                    # Must have a valid Steam ID 64 to appear in squad.xml
                    if not is_valid_steam_id64(person.steamId64 or ""):
                        if person.steamId64:
                            logger.warning(
                                "Skipping %s (perscomId=%s): invalid steamId64 %r",
                                person.name,
                                person.perscomId,
                                person.steamId64,
                            )
                        continue

                    # Filter by status
                    if person.status is None or person.status.id not in status_ids:
                        continue

                    # Optional unit filter
                    if unit_ids and (person.unit is None or person.unit.id not in unit_ids):
                        continue

                    results.append(person)

                if len(batch) < _PAGE_SIZE or (offset + len(batch)) >= total:
                    break

                offset += _PAGE_SIZE

        logger.info("Fetched %d active personnel with Steam IDs", len(results))
        return results
