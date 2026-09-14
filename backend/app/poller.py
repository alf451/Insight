"""Background polling: SSTProt is a poll-based protocol (unlike MQTT), so
"real-time monitoring" here means "poll on an interval and push what
changed" rather than a subscription. One asyncio task per enabled device;
a failure on one device (unreachable, timeout, NA) never stops the others
(spec principle: isolate devices from each other).
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from starlette.websockets import WebSocket

from . import models
from .db import session_scope
from .sstprot import commands as cmd
from .sstprot.connector import SstProtConnector
from .sstprot.frame import SstProtError

logger = logging.getLogger("insight.poller")

LOGBOOK_SYNC_BATCH = 5
"""Entries to check for new ones on each poll. Each entry costs one "LE"
command, and SSTProt recommends >=200ms between commands (see connector.py)
— a full poll of read_device_data() (~10 commands) plus this logbook sync
already takes several seconds. Keep this small; it only needs to cover how
many *new* logbook entries could plausibly appear between two polls."""


@dataclass
class DeviceLiveState:
    latest: Optional[dict] = None
    last_error: Optional[str] = None
    last_updated: Optional[str] = None
    connected: bool = False
    subscribers: set[WebSocket] = field(default_factory=set)


class PollerManager:
    def __init__(self) -> None:
        self.states: dict[int, DeviceLiveState] = {}
        self._tasks: dict[int, asyncio.Task] = {}

    def get_state(self, device_id: int) -> DeviceLiveState:
        return self.states.setdefault(device_id, DeviceLiveState())

    def start(self, device: models.Device) -> None:
        if device.id in self._tasks:
            return
        self.get_state(device.id)
        self._tasks[device.id] = asyncio.create_task(self._run(device.id, device.host, device.port, device.address, device.poll_interval_s))

    def stop(self, device_id: int) -> None:
        task = self._tasks.pop(device_id, None)
        if task:
            task.cancel()

    def stop_all(self) -> None:
        for device_id in list(self._tasks):
            self.stop(device_id)

    async def _run(self, device_id: int, host: str, port: int, address: str, interval_s: float) -> None:
        while True:
            data = None
            try:
                data = await asyncio.to_thread(self._poll_once, device_id, host, port, address)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # a broken device must never kill the poller
                state = self.get_state(device_id)
                state.connected = False
                state.last_error = str(exc)
                logger.warning("device %s poll failed: %s", device_id, exc)
            if data is not None:
                # broadcasting schedules asyncio tasks, so it must happen
                # back on the event-loop thread, not inside the to_thread worker.
                self._broadcast(device_id, data)
            await asyncio.sleep(interval_s)

    def _poll_once(self, device_id: int, host: str, port: int, address: str) -> dict:
        state = self.get_state(device_id)
        with SstProtConnector(host, port=port, address=address) as conn:
            data = cmd.read_device_data(conn)
            self._archive_reading(device_id, data)
            try:
                entries = cmd.read_logbook(conn, max_entries=LOGBOOK_SYNC_BATCH)
                self._archive_logbook(device_id, entries)
            except SstProtError as exc:
                logger.info("device %s logbook sync skipped: %s", device_id, exc)

        state.latest = data
        state.connected = True
        state.last_error = None
        state.last_updated = datetime.now(timezone.utc).isoformat()
        return data

    @staticmethod
    def _archive_reading(device_id: int, data: dict) -> None:
        status = data["system_status"]
        product = data["product_data"]
        counters = data["global_counters"]
        with session_scope() as session:
            session.add(
                models.DeviceReading(
                    device_id=device_id,
                    main_state=status["main_state"],
                    main_state_name=status["main_state_name"],
                    metal_signal=status["metal_signal"],
                    error_status=status["error_status"],
                    flags=status["flags"],
                    current_product_number=data["current_product_number"],
                    sensitivity=product["sensitivity"],
                    product_angle=product["product_angle"],
                    gain=product["gain"],
                    threshold=product["threshold"],
                    conveyor_speed=product["conveyor_speed"],
                    error_counter=counters["error_counter"],
                    metal_counter=counters["metal_counter"],
                    product_counter=counters["product_counter"],
                    raw=data,
                )
            )

    @staticmethod
    def _archive_logbook(device_id: int, entries: list[dict]) -> None:
        with session_scope() as session:
            existing = {
                n
                for (n,) in session.query(models.LogbookEntryRow.absolute_number)
                .filter(models.LogbookEntryRow.device_id == device_id)
                .all()
            }
            for entry in entries:
                abs_num = entry.get("absolute_number")
                if abs_num is None or abs_num in existing:
                    continue
                session.add(
                    models.LogbookEntryRow(
                        device_id=device_id,
                        absolute_number=abs_num,
                        timestamp=entry["timestamp"],
                        entry_code=entry["entry_code"],
                        entry_code_description=entry["entry_code_description"],
                        decoded=entry["decoded"],
                    )
                )
                existing.add(abs_num)

    def _broadcast(self, device_id: int, data: dict) -> None:
        state = self.get_state(device_id)
        dead = set()
        for ws in state.subscribers:
            try:
                asyncio.create_task(ws.send_json({"device_id": device_id, "data": data}))
            except Exception:
                dead.add(ws)
        state.subscribers -= dead


poller = PollerManager()
