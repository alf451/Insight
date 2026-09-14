from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models
from .db import SessionLocal, init_db, session_scope
from .poller import poller
from .schemas import DeviceCreate, DeviceOut, DeviceUpdate, SetSensitivityRequest
from .sstprot import commands as cmd
from .sstprot.connector import SstProtConnector
from .sstprot.frame import SstProtError


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with session_scope() as session:
        for device in session.query(models.Device).filter(models.Device.enabled.is_(True)).all():
            poller.start(device)
    yield
    poller.stop_all()


app = FastAPI(title="Insight — SSTProt backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Device configuration ("frontend di mappatura e configurazione connessione")
# ---------------------------------------------------------------------------


@app.get("/api/devices", response_model=list[DeviceOut])
def list_devices(db: Session = Depends(get_db)):
    return db.query(models.Device).all()


@app.post("/api/devices", response_model=DeviceOut)
async def create_device(payload: DeviceCreate, db: Session = Depends(get_db)):
    device = models.Device(**payload.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    if device.enabled:
        poller.start(device)
    return device


@app.put("/api/devices/{device_id}", response_model=DeviceOut)
async def update_device(device_id: int, payload: DeviceUpdate, db: Session = Depends(get_db)):
    device = db.get(models.Device, device_id)
    if not device:
        raise HTTPException(404, "device not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(device, key, value)
    db.commit()
    db.refresh(device)

    poller.stop(device_id)
    if device.enabled:
        poller.start(device)
    return device


@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.get(models.Device, device_id)
    if not device:
        raise HTTPException(404, "device not found")
    poller.stop(device_id)
    db.delete(device)
    db.commit()
    return {"ok": True}


@app.post("/api/devices/{device_id}/test")
def test_connection(device_id: int, db: Session = Depends(get_db)):
    device = db.get(models.Device, device_id)
    if not device:
        raise HTTPException(404, "device not found")
    try:
        with SstProtConnector(device.host, port=device.port, address=device.address, timeout=3.0) as conn:
            info = cmd.get_device_info(conn)
        return {"ok": True, "device_info": info}
    except (SstProtError, OSError) as exc:
        return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Monitoring ("frontend monitoraggio dei dati ricevuti dal metal detector")
# ---------------------------------------------------------------------------


@app.get("/api/devices/{device_id}/latest")
def get_latest(device_id: int):
    state = poller.get_state(device_id)
    return {
        "connected": state.connected,
        "last_error": state.last_error,
        "last_updated": state.last_updated,
        "data": state.latest,
    }


@app.get("/api/devices/{device_id}/readings")
def get_readings(device_id: int, limit: int = 100, db: Session = Depends(get_db)):
    rows = (
        db.query(models.DeviceReading)
        .filter(models.DeviceReading.device_id == device_id)
        .order_by(models.DeviceReading.timestamp.desc())
        .limit(min(limit, 1000))
        .all()
    )
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "main_state_name": r.main_state_name,
            "sensitivity": r.sensitivity,
            "product_angle": r.product_angle,
            "gain": r.gain,
            "threshold": r.threshold,
            "metal_counter": r.metal_counter,
            "error_counter": r.error_counter,
        }
        for r in rows
    ]


@app.get("/api/devices/{device_id}/logbook")
def get_logbook(device_id: int, limit: int = 100, db: Session = Depends(get_db)):
    rows = (
        db.query(models.LogbookEntryRow)
        .filter(models.LogbookEntryRow.device_id == device_id)
        .order_by(models.LogbookEntryRow.absolute_number.desc())
        .limit(min(limit, 1000))
        .all()
    )
    return [
        {
            "absolute_number": r.absolute_number,
            "timestamp": r.timestamp,
            "entry_code": r.entry_code,
            "entry_code_description": r.entry_code_description,
            "decoded": r.decoded,
        }
        for r in rows
    ]


@app.websocket("/ws/devices/{device_id}")
async def ws_device(websocket: WebSocket, device_id: int):
    await websocket.accept()
    state = poller.get_state(device_id)
    state.subscribers.add(websocket)
    try:
        if state.latest is not None:
            await websocket.send_json({"device_id": device_id, "data": state.latest})
        while True:
            await websocket.receive_text()  # keep the connection open; client sends nothing meaningful
    except WebSocketDisconnect:
        pass
    finally:
        state.subscribers.discard(websocket)


# ---------------------------------------------------------------------------
# Write examples ("esempio di scrittura dato al metaldetector")
# ---------------------------------------------------------------------------


@app.post("/api/devices/{device_id}/write/system-time")
def write_system_time(device_id: int, db: Session = Depends(get_db)):
    """SAFE write example: syncs the device clock to the server's current
    time. Documented per SSTProt 'TT' set command."""
    device = db.get(models.Device, device_id)
    if not device:
        raise HTTPException(404, "device not found")
    try:
        with SstProtConnector(device.host, port=device.port, address=device.address) as conn:
            ok = cmd.set_system_time(conn, datetime.now(timezone.utc))
        return {"ok": ok}
    except (SstProtError, OSError) as exc:
        raise HTTPException(502, str(exc))


@app.post("/api/devices/{device_id}/write/sensitivity")
def write_sensitivity(device_id: int, payload: SetSensitivityRequest, db: Session = Depends(get_db)):
    """WRITE example for the domain's most important variable. Gated
    behind `confirm=true` on purpose — see docs/SSTPROT.md: this changes
    what the metal detector rejects and has not been exercised against
    real hardware in this project."""
    if not payload.confirm:
        raise HTTPException(400, "set confirm=true to actually write to the device")
    device = db.get(models.Device, device_id)
    if not device:
        raise HTTPException(404, "device not found")
    try:
        with SstProtConnector(device.host, port=device.port, address=device.address) as conn:
            current = cmd.get_product_data(conn, payload.product_number)
            ok = cmd.set_product_data(
                conn,
                product_number=payload.product_number,
                sensitivity=payload.sensitivity,
                product_angle=current["product_angle"],
                frequency_index=current["frequency_index"],
                blanking=current["blanking"],
                options=current["options"],
                conveyor_speed=current["conveyor_speed"],
                gain=current["gain"],
                threshold=current["threshold"],
            )
            readback = cmd.get_product_data(conn, payload.product_number)
        return {"ok": ok, "readback": readback}
    except (SstProtError, OSError) as exc:
        raise HTTPException(502, str(exc))
