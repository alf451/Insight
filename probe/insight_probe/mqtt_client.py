"""MQTT client wrapper for the Discovery Probe.

READ ONLY BY DESIGN: this module exposes connect/disconnect/subscribe only.
There is intentionally no publish() method anywhere in the Probe — the Probe
must never write to the metal detector (spec sections 6 and 27).

Built on paho-mqtt (classic 1.6.x callback API: on_connect(client, userdata,
flags, rc), on_message(client, userdata, msg)) for broad compatibility with
MQTT 3.1.1 and MQTT 5 brokers.
"""
from __future__ import annotations

import queue
import ssl
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import paho.mqtt.client as mqtt

from .models import MessageRecord, utcnow_iso


class ConnectionState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"


# paho-mqtt reason codes we translate into human-readable diagnostics.
_CONNACK_MESSAGES = {
    0: "Connection accepted",
    1: "Connection refused - incorrect protocol version",
    2: "Connection refused - invalid client identifier",
    3: "Connection refused - server unavailable",
    4: "Connection refused - bad username or password",
    5: "Connection refused - not authorised",
}


@dataclass
class MqttProbeConfig:
    broker_host: str
    broker_port: int = 1883
    protocol_version: str = "3.1.1"  # "3.1.1" or "5"
    username: Optional[str] = None
    password: Optional[str] = None
    tls_enabled: bool = False
    ca_certificate: Optional[str] = None
    client_certificate: Optional[str] = None
    client_key: Optional[str] = None
    keepalive: int = 60
    connect_timeout_s: float = 10.0
    reconnect_enabled: bool = True
    reconnect_min_delay_s: float = 1.0
    reconnect_max_delay_s: float = 60.0
    subscription_topic: str = "#"
    qos: int = 0
    client_id: str = ""


@dataclass
class ConnectionStatus:
    state: ConnectionState = ConnectionState.DISCONNECTED
    detail: str = ""
    connected_since: Optional[str] = None
    last_error: Optional[str] = None


class ProbeMqttClient:
    """Thread-safe-enough wrapper: paho runs its network loop on its own
    thread; incoming messages are handed off via a queue.Queue so the
    Tkinter main thread can poll them safely instead of touching widgets
    from a background thread.
    """

    def __init__(self, config: MqttProbeConfig, connection_id: str) -> None:
        self.config = config
        self.connection_id = connection_id
        self.status = ConnectionStatus()
        self.message_queue: "queue.Queue[MessageRecord]" = queue.Queue()
        self._status_lock = threading.Lock()
        self._client = self._build_client()

    # -- setup -----------------------------------------------------------

    def _build_client(self) -> mqtt.Client:
        protocol = mqtt.MQTTv5 if self.config.protocol_version == "5" else mqtt.MQTTv311
        client = mqtt.Client(
            client_id=self.config.client_id or f"insight-probe-{int(time.time())}",
            protocol=protocol,
        )

        if self.config.username:
            client.username_pw_set(self.config.username, self.config.password or None)

        if self.config.tls_enabled:
            client.tls_set(
                ca_certs=self.config.ca_certificate or None,
                certfile=self.config.client_certificate or None,
                keyfile=self.config.client_key or None,
                cert_reqs=ssl.CERT_REQUIRED if self.config.ca_certificate else ssl.CERT_NONE,
            )

        if self.config.reconnect_enabled:
            client.reconnect_delay_set(
                min_delay=self.config.reconnect_min_delay_s,
                max_delay=self.config.reconnect_max_delay_s,
            )

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        return client

    # -- callbacks (run on paho's network thread) -------------------------

    def _on_connect(self, client, userdata, flags, rc, properties=None) -> None:
        with self._status_lock:
            if rc == 0:
                self.status.state = ConnectionState.CONNECTED
                self.status.detail = _CONNACK_MESSAGES.get(rc, f"Connected (rc={rc})")
                self.status.connected_since = utcnow_iso()
                self.status.last_error = None
            else:
                self.status.state = ConnectionState.ERROR
                self.status.last_error = _CONNACK_MESSAGES.get(rc, f"Connection failed (rc={rc})")
        if rc == 0:
            client.subscribe(self.config.subscription_topic, qos=self.config.qos)

    def _on_disconnect(self, client, userdata, rc, properties=None) -> None:
        with self._status_lock:
            self.status.state = ConnectionState.DISCONNECTED
            if rc != 0:
                self.status.last_error = f"Unexpected disconnect (rc={rc})"

    def _on_message(self, client, userdata, msg) -> None:
        try:
            payload_text = msg.payload.decode("utf-8", errors="replace")
        except Exception as exc:  # never let a bad payload kill the network thread
            payload_text = f"<undecodable payload: {exc}>"
        record = MessageRecord(
            timestamp=utcnow_iso(),
            topic=msg.topic,
            qos=msg.qos,
            retain=bool(msg.retain),
            payload=payload_text,
            connection_id=self.connection_id,
            client_id=self._client._client_id.decode("utf-8", errors="replace")
            if isinstance(self._client._client_id, bytes)
            else str(self._client._client_id),
        )
        self.message_queue.put(record)

    # -- public API --------------------------------------------------------

    def connect(self) -> None:
        with self._status_lock:
            self.status.state = ConnectionState.CONNECTING
            self.status.detail = f"Connecting to {self.config.broker_host}:{self.config.broker_port}"
            self.status.last_error = None
        try:
            self._client.connect_async(
                self.config.broker_host,
                self.config.broker_port,
                keepalive=self.config.keepalive,
            )
            self._client.loop_start()
        except Exception as exc:
            with self._status_lock:
                self.status.state = ConnectionState.ERROR
                self.status.last_error = str(exc)

    def disconnect(self) -> None:
        try:
            self._client.loop_stop()
            self._client.disconnect()
        finally:
            with self._status_lock:
                self.status.state = ConnectionState.DISCONNECTED

    def drain_messages(self, max_items: int = 500) -> list[MessageRecord]:
        """Non-blocking pull of everything queued since the last call."""
        items: list[MessageRecord] = []
        for _ in range(max_items):
            try:
                items.append(self.message_queue.get_nowait())
            except queue.Empty:
                break
        return items

    def get_status(self) -> ConnectionStatus:
        with self._status_lock:
            return ConnectionStatus(**self.status.__dict__)
