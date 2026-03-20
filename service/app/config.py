from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PERSCOM API connection
    perscom_api_url: str = "https://api.1stcavalry.org"
    perscom_api_key: str

    # Comma-separated status IDs to include in squad.xml.
    # Defaults to 1 (Active Duty) based on the API example.
    active_status_ids: str = "1"

    # Optional comma-separated unit IDs to restrict to. Empty = all units.
    filter_unit_ids: str = ""

    # Squad-level metadata written into squad.xml
    squad_tag: str = "1CAV"
    squad_name: str = "1st Cavalry Division"
    squad_email: str = "admin@1stcavalry.org"
    squad_web: str = "https://1stcavalry.org"
    squad_title: str = "1st Cavalry Division - Arma 3 MilSim"

    # Filename (without path) of the PAA logo placed in service/static/.
    # Leave empty if you have no logo file.
    logo_filename: Optional[str] = None

    # How often (seconds) to re-sync from PERSCOM
    sync_interval: int = 300  # 5 minutes

    # Secret key required to hit POST /sync manually
    sync_key: str = "change-me"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
