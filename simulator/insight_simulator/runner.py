"""MQTT publishing loop + interactive stdin command console for the mock
metal detector. Kept separate from mock_metal_detector.py so the state
machine stays unit-testable without a broker.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time

import paho.mqtt.client as mqtt

from .mock_metal_detector import MockMetalDetector

HELP_TEXT = """
Commands:
  start                    set running=true
  stop                     set running=false
  article <name>           change current article
  lot <name>               change current lot
  sensitivity fe <value>   set FE sensitivity
  sensitivity nonfe <value>
  sensitivity stainless <value>
  detect                   publish a DETECTION event
  reject                   publish a DETECTION event with rejected=true
  alarm [reason]           publish an ALARM event
  help                     show this text
  quit                     stop the simulator
"""


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Insight Mock Metal Detector Simulator")
    parser.add_argument("--broker", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--device-id", default="MD-SIM-01")
    parser.add_argument("--topic-prefix", default="insight/sim")
    parser.add_argument("--interval", type=float, default=2.0, help="status publish interval (seconds)")
    parser.add_argument("--qos", type=int, default=0)
    return parser


class SimulatorRunner:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.detector = MockMetalDetector(device_id=args.device_id)
        self.client = mqtt.Client(client_id=f"insight-sim-{args.device_id}")
        self._stop_event = threading.Event()

    def status_topic(self) -> str:
        return f"{self.args.topic_prefix}/{self.args.device_id}/status"

    def event_topic(self) -> str:
        return f"{self.args.topic_prefix}/{self.args.device_id}/event"

    def connect(self) -> None:
        self.client.connect(self.args.broker, self.args.port, keepalive=60)
        self.client.loop_start()

    def publish_status(self) -> None:
        payload = json.dumps(self.detector.build_status_payload())
        self.client.publish(self.status_topic(), payload, qos=self.args.qos, retain=False)

    def publish_event(self, payload: dict) -> None:
        self.client.publish(self.event_topic(), json.dumps(payload), qos=self.args.qos, retain=False)

    def _status_loop(self) -> None:
        while not self._stop_event.is_set():
            self.publish_status()
            self._stop_event.wait(self.args.interval)

    def _handle_command(self, line: str) -> bool:
        """Returns False if the simulator should stop."""
        parts = line.strip().split()
        if not parts:
            return True
        cmd, *rest = parts
        cmd = cmd.lower()

        if cmd == "quit":
            return False
        if cmd == "help":
            print(HELP_TEXT)
        elif cmd == "start":
            self.detector.start()
            print("running = true")
        elif cmd == "stop":
            self.detector.stop()
            print("running = false")
        elif cmd == "article" and rest:
            self.detector.set_article(rest[0])
            print(f"article = {rest[0]}")
        elif cmd == "lot" and rest:
            self.detector.set_lot(rest[0])
            print(f"lot = {rest[0]}")
        elif cmd == "sensitivity" and len(rest) == 2:
            try:
                self.detector.set_sensitivity(rest[0], float(rest[1]))
                print(f"sensitivity {rest[0]} = {rest[1]}")
            except ValueError as exc:
                print(f"error: {exc}")
        elif cmd == "detect":
            self.publish_event(self.detector.trigger_detection(rejected=False))
            print("published DETECTION")
        elif cmd == "reject":
            self.publish_event(self.detector.trigger_detection(rejected=True))
            print("published DETECTION (rejected=true)")
        elif cmd == "alarm":
            reason = rest[0] if rest else "TEST"
            self.publish_event(self.detector.trigger_alarm(reason))
            print(f"published ALARM reason={reason}")
        else:
            print(f"unknown command: {line!r} (type 'help')")
        return True

    def run(self) -> None:
        self.connect()
        status_thread = threading.Thread(target=self._status_loop, daemon=True)
        status_thread.start()

        print(f"Publishing status to {self.status_topic()} every {self.args.interval}s")
        print(f"Publishing events to {self.event_topic()}")
        print(HELP_TEXT)

        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    time.sleep(0.2)
                    continue
                if not self._handle_command(line):
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self._stop_event.set()
            self.client.loop_stop()
            self.client.disconnect()


def main(argv=None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    SimulatorRunner(args).run()
