"""Lookup tables transcribed from the official SSTProt V1.54.pdf.
Every value here has a page reference in the source PDF — nothing guessed.
"""

# Page 10 — "get device type" (DT)
DEVICE_TYPE_NAMES = {
    0x01: "SensityII",
    0x03: "Genius",
    0x04: "Primus",
    0x05: "Genius+",
    0x06: "MSG3.4K",
    0x20: "GeniusTouch",
    0x30: "Raycon XRS",
    0x40: "INTUITY",
    0x50: "GeniusOne",
}

# Page 22 — Main State Code (Genius+/GeniusOne)
MAIN_STATE_NAMES = {
    0x00: "IDLE",
    0x01: "TEST",
    0x02: "LEARNING",
    0x03: "DUMMY1",
    0x04: "ERROR",
    0x05: "WARNING",
    0x06: "SETUP",
}

# Page 23 — Flags Code (Genius+/GeniusOne, SQ command)
FLAGS_BITS = {
    0x01: "Operation Status ON",
    0x02: "Any error",
    0x04: "Metal Status",
    0x08: "Operation Status Blinking",
    0x10: "New Logbook Entry",
    0x20: "Detected",
    0x40: "Sync",
    0x80: "Service User Logged In",
}

# Page 23 — Error Status Code (Genius+/GeniusOne, SQ command, u32 bitmask)
ERROR_STATUS_BITS = {
    0x00000001: "ERROR_RECV_TO_HIGH",
    0x00000002: "ERROR_TX_OVERTEMPERATURE",
    0x00000004: "ERROR_WDOG_AWE",
    0x00000008: "ERROR_COMMUNICATION_AWE",
    0x00000010: "ERROR_OVERLOAD_24V",
    0x00000020: "ERROR_INITIATOR_BROKEN",
    0x00000040: "ERROR_FLAP_POSITION",
    0x00000080: "ERROR_AIR_PRESSURE",
    0x00000100: "ERROR_CONVEYOR_CONTROL",
    0x00000200: "ERROR_CONTAINER_FULL",
    0x00000400: "ERROR_EJECT_CONTROL",
    0x00000800: "ERROR_LIGHT_BARRIER",
    0x00001000: "ERROR_AUTO_CHECK",
    0x00002000: "ERROR_EEPROM",
    0x00004000: "ERROR_TEST_NOK",
    0x00008000: "ERROR_TEST_TMO",
    0x00010000: "ERROR_EVA_HW",
    0x00020000: "ERROR_METAL_BURST",
    0x00040000: "ERROR_EXTERNAL",
    0x00080000: "ERROR_REJECT_BIN",
    0x00100000: "ERROR_REJECT_CHECK",
    0x00200000: "ERROR_OTHER",
}

# Page 46-47 — Logbook Entries, Genius+ / INTUITY / Genius One ("LE" command)
# name -> (entry_code, param_meanings) where param_meanings maps
# "Parameter N" (1-indexed) to a human label. Params not listed for a given
# code are not meaningful for that entry type (protocol always sends 4
# u16 slots regardless — see commands.py).
LOGBOOK_ENTRY_CODES = {
    0x01: ("Rilevazione metallo", {1: "Numero prodotto", 2: "Segnale metallo", 3: "Contatore metallo tot.", 4: "Soglia"}),
    0x02: ("Errore: Receiver to high", {1: "Contatore errori tot."}),
    0x03: ("Errore: TX overtemperature", {1: "Contatore errori tot."}),
    0x04: ("Errore: Watchdog AWE", {1: "Contatore errori tot."}),
    0x05: ("Errore: Communication AWE", {1: "Contatore errori tot."}),
    0x06: ("Errore: Overload 24V output", {1: "Contatore errori tot."}),
    0x07: ("Errore: Initiator broken", {1: "Contatore errori tot."}),
    0x08: ("Errore: Flap position", {1: "Contatore errori tot."}),
    0x09: ("Errore: Air pressure", {1: "Contatore errori tot."}),
    0x0A: ("Errore: Conveyor control", {1: "Contatore errori tot."}),
    0x0B: ("Errore: Container full", {1: "Contatore errori tot."}),
    0x0C: ("Errore: Eject control", {1: "Contatore errori tot."}),
    0x0D: ("Errore: Light barrier", {1: "Contatore errori tot."}),
    0x0E: ("Errore: Auto check", {1: "Contatore errori tot."}),
    0x0F: ("Errore: EEProm failure", {1: "Contatore errori tot."}),
    0x10: ("Errore: Test not ok", {1: "Contatore errori tot."}),
    0x11: ("Errore: Test timeout", {1: "Contatore errori tot."}),
    0x12: ("Errore: Hardware AWE", {1: "Contatore errori tot."}),
    0x13: ("Errore: Metal burst", {1: "Contatore errori tot."}),
    0x14: ("Errore: External error", {1: "Contatore errori tot."}),
    0x15: ("Errore: Reject Bin", {1: "Contatore errori tot."}),
    0x16: ("Errore: Reject Check", {1: "Contatore errori tot."}),
    0x17: ("Errore: Any other error", {1: "Contatore errori tot."}),
    0x40: ("Warning: Battery low", {}),
    0x41: ("Logbook quasi pieno", {}),
    0x42: ("Warning: Temperature sensor", {}),
    0x43: ("Warning: TX temperature", {}),
    0x44: ("Warning: Receiver too high", {}),
    0x45: ("Warning: EEProm value comparison", {}),
    0x46: ("Warning: Product distance too short", {}),
    0x80: ("Accensione", {}),
    0x81: ("Spegnimento", {}),
    0x82: ("Cambio prodotto", {1: "Nuovo numero prodotto", 4: "Vecchio numero prodotto"}),
    0x83: ("Dati prodotto modificati", {1: "Numero prodotto corrente", 2: "Sensibilita'", 3: "Angolo"}),
    0x85: ("Cambio lotto (batch)", {}),
    0x86: ("Stato output", {1: "Stato (0=inattivo, 1=attivo)"}),
    0x87: ("Quicklearn", {1: "Angolo"}),
    0x88: ("Richiesta test", {}),
    0x89: ("Avvio test", {}),
    0x8A: ("Risultato test", {1: "Pezzo di test", 2: "Part ID", 3: "Risultato"}),
    0x8B: ("Fine test", {1: "Risultato"}),
    0x8C: ("Test automatico", {}),
    0x8D: ("Data/ora modificate", {}),
    0x8E: ("EEProm reinizializzata", {1: "Tipo (1=Sistema, 2=Prodotto)", 2: "Numero prodotto"}),
    0x8F: ("Rilevazione metallo (durante test)", {1: "Segnale metallo"}),
    0x90: ("Dati sistema modificati", {1: "Gruppo parametri"}),
    0x91: ("Bypass", {1: "Stato (0=inattivo, 1=attivo)"}),
    0x92: ("Reset errore", {}),
    0x93: ("Utente connesso", {1: "ID utente"}),
    0x94: ("Utente disconnesso", {1: "ID utente"}),
    0x95: ("Richiesta test esterna", {}),
    0x96: ("Test reject esterno", {}),
    0x97: ("Nessuna modifica prodotto nel logbook", {}),
    0xC0: ("Internal watchdog expired", {1: "Numero task"}),
    0xC1: ("Com AWE timeout", {1: "Contatore"}),
    0xC2: ("STE Reboot", {}),
    0xFE: ("Voce non mappata", {}),
}


def describe_entry_code(code: int) -> str:
    entry = LOGBOOK_ENTRY_CODES.get(code)
    return entry[0] if entry else f"UNKNOWN (0x{code:02X})"


def decode_flags(flags: int) -> list[str]:
    return [name for bit, name in FLAGS_BITS.items() if flags & bit]


def decode_error_status(error_status: int) -> list[str]:
    return [name for bit, name in ERROR_STATUS_BITS.items() if error_status & bit]
