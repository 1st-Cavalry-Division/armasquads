from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class PerscomRank(BaseModel):
    id: int
    name: str
    abbreviation: Optional[str] = None
    rankOrder: Optional[int] = None


class PerscomPosition(BaseModel):
    id: int
    name: str


class PerscomSpecialty(BaseModel):
    id: int
    name: str
    abbreviation: Optional[str] = None


class PerscomStatus(BaseModel):
    id: int
    name: str
    color: Optional[str] = None
    label: Optional[str] = None


class PerscomUnit(BaseModel):
    id: int
    name: str


class PerscomPersonnel(BaseModel):
    id: str  # UUID
    perscomId: int
    name: str
    email: Optional[str] = None
    steamId64: Optional[str] = None
    approved: Optional[bool] = None
    rank: Optional[PerscomRank] = None
    position: Optional[PerscomPosition] = None
    specialty: Optional[PerscomSpecialty] = None
    status: Optional[PerscomStatus] = None
    unit: Optional[PerscomUnit] = None
    country: Optional[str] = None
    online: Optional[bool] = None

    model_config = {"extra": "ignore"}


class SquadMember(BaseModel):
    steam_id: str
    nick: str
    name: str
    email: str
    remark: str


class SquadData(BaseModel):
    tag: str
    name: str
    email: str
    web: str
    title: str
    logo: Optional[str]
    members: List[SquadMember]
    last_sync: Optional[datetime] = None
