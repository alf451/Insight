from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DeviceCreate(BaseModel):
    name: str
    host: str
    port: int = 10001
    address: str = "FF"
    poll_interval_s: float = 5.0
    enabled: bool = True


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    address: Optional[str] = None
    poll_interval_s: Optional[float] = None
    enabled: Optional[bool] = None


class DeviceOut(BaseModel):
    id: int
    name: str
    host: str
    port: int
    address: str
    poll_interval_s: float
    enabled: bool

    model_config = {"from_attributes": True}


class SetSensitivityRequest(BaseModel):
    """WRITE example — spec asked for one explicitly. Gated behind
    `confirm=true` because this changes what the metal detector actually
    rejects; see docs/SSTPROT.md before using against a real device."""

    product_number: int
    sensitivity: int = Field(ge=1, le=100)
    confirm: bool = False
