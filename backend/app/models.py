"""ORM models.

Kept intentionally small: this archives what the SSTProt connector reads
(spec's "archiviazione dati letti") and holds device connection config
(spec's device mapping/configuration). It's a subset of the full schema
sketched in docs/DATABASE.md (production sessions, articles/lots, audit
log, RBAC, ...) — those are still Fase 5+ and NOT built here; see
docs/ROADMAP.md.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer, default=10001)
    address: Mapped[str] = mapped_column(String(2), default="FF")
    poll_interval_s: Mapped[float] = mapped_column(Float, default=5.0)
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    readings: Mapped[list["DeviceReading"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    logbook_entries: Mapped[list["LogbookEntryRow"]] = relationship(back_populates="device", cascade="all, delete-orphan")


class DeviceReading(Base):
    """One archived snapshot of read_device_data(), SYSTEMATIC mode (every
    poll is stored) — see docs/ROADMAP.md for CHANGE-mode as a later
    refinement once real polling volume is known."""

    __tablename__ = "device_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    main_state: Mapped[int] = mapped_column(Integer)
    main_state_name: Mapped[str] = mapped_column(String(20))
    metal_signal: Mapped[int] = mapped_column(Integer)
    error_status: Mapped[int] = mapped_column(Integer)
    flags: Mapped[int] = mapped_column(Integer)

    current_product_number: Mapped[int] = mapped_column(Integer)
    sensitivity: Mapped[int] = mapped_column(Integer)
    product_angle: Mapped[int] = mapped_column(Integer)
    gain: Mapped[int] = mapped_column(Integer)
    threshold: Mapped[int] = mapped_column(Integer)
    conveyor_speed: Mapped[int] = mapped_column(Integer)

    error_counter: Mapped[int] = mapped_column(Integer)
    metal_counter: Mapped[int] = mapped_column(Integer)
    product_counter: Mapped[int] = mapped_column(Integer)

    raw: Mapped[dict] = mapped_column(JSON)
    """Full read_device_data() dict — belt-and-braces so nothing is lost
    even for fields not promoted to their own column."""

    device: Mapped[Device] = relationship(back_populates="readings")


class LogbookEntryRow(Base):
    __tablename__ = "logbook_entries"
    __table_args__ = (UniqueConstraint("device_id", "absolute_number", name="uq_device_logbook_entry"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    absolute_number: Mapped[int] = mapped_column(Integer, index=True)
    timestamp: Mapped[str] = mapped_column(String(30))
    entry_code: Mapped[int] = mapped_column(Integer)
    entry_code_description: Mapped[str] = mapped_column(String(100))
    decoded: Mapped[dict] = mapped_column(JSON)
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    device: Mapped[Device] = relationship(back_populates="logbook_entries")
