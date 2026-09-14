"""End-to-end tests against the mock GeniusOne TCP server
(simulator/insight_simulator/sstprot_server.py), seeded with values taken
verbatim from a real captured session (sstprot_function_final_report.md).
A pass here is a genuine cross-check against real device output, not just
internal self-consistency.
"""
import threading

import pytest

from app.sstprot import commands as cmd
from app.sstprot.connector import SstProtConnector
from insight_simulator.sstprot_server import SstProtTestServer


@pytest.fixture()
def connector():
    server = SstProtTestServer("127.0.0.1", 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    with SstProtConnector("127.0.0.1", port=port, address="01", inter_command_delay=0.0) as conn:
        yield conn
    server.shutdown()


def test_read_device_data_matches_real_report_example(connector):
    data = cmd.read_device_data(connector)

    assert data["device_info"]["address"] == 1
    assert data["device_info"]["device_type_name"] == "GeniusOne"
    assert data["system_status"]["main_state_name"] == "WARNING"
    assert data["system_status"]["flags"] == 145
    assert set(data["system_status"]["active_flags"]) == {
        "Operation Status ON",
        "New Logbook Entry",
        "Service User Logged In",
    }
    assert data["current_product_number"] == 16
    assert data["product_data"] == {
        "product_number": 16,
        "sensitivity": 85,
        "product_angle": 1382,
        "frequency_index": 0,
        "blanking": 0,
        "options": 0,
        "conveyor_speed": 11,
        "gain": 184,
        "threshold": 20,
    }
    assert data["global_counters"]["error_counter"] == 284
    assert data["global_counters"]["metal_counter"] == 247910
    assert data["logbook_max"] == 1500
    assert data["logbook_count"] == 1500


def test_read_logbook_matches_real_report_example(connector):
    entries = cmd.read_logbook(connector, max_entries=30)
    assert len(entries) == 30

    assert entries[0]["entry_code"] == 0x90
    assert entries[0]["entry_code_description"] == "Dati sistema modificati"

    metal_entry = entries[8]
    assert metal_entry["entry_code"] == 0x01
    assert metal_entry["entry_code_description"] == "Rilevazione metallo"
    assert metal_entry["timestamp"] == "2026-05-15 05:30:31"
    assert metal_entry["decoded"] == {
        "Numero prodotto": 16,
        "Segnale metallo": 159,
        "Contatore metallo tot.": 51302,
        "Soglia": 0,
    }


def test_write_system_time(connector):
    assert cmd.set_system_time(connector) is True


def test_write_product_sensitivity_roundtrip(connector):
    assert cmd.set_product_data(
        connector,
        product_number=16,
        sensitivity=90,
        product_angle=1382,
        frequency_index=0,
        blanking=0,
        options=0,
        conveyor_speed=11,
        gain=184,
        threshold=20,
    )
    updated = cmd.get_product_data(connector, 16)
    assert updated["sensitivity"] == 90
