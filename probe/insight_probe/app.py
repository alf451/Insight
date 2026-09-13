"""Insight MQTT Discovery Probe — Tkinter GUI.

Read-only discovery tool for use at the client site (spec sections 6, 7).
No publish/write capability exists anywhere in this application.

Run with: python -m insight_probe
"""
from __future__ import annotations

import json
import tkinter as tk
import traceback
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

from .capture import append_capture, capture_filename, write_capture
from .device_profile import build_device_profile, save_device_profile
from .models import EVENT_TYPES, MessageRecord
from .mqtt_client import ConnectionState, MqttProbeConfig, ProbeMqttClient
from .registry import DiscoveryRegistry

POLL_INTERVAL_MS = 200
MAX_VISIBLE_MESSAGES = 2000


class ProbeApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Insight MQTT Discovery Probe")
        self.root.geometry("1200x800")

        self.registry = DiscoveryRegistry()
        self.mqtt_client: Optional[ProbeMqttClient] = None
        self.capture_active = False
        self.capture_path: Optional[Path] = None
        self._selected_message: Optional[MessageRecord] = None

        self._build_connection_frame()
        self._build_control_frame()
        self._build_notebook()
        self._build_status_bar()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(POLL_INTERVAL_MS, self._poll)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_connection_frame(self) -> None:
        frame = ttk.LabelFrame(self.root, text="MQTT Connection")
        frame.pack(fill="x", padx=6, pady=4)

        def add_field(row, col, label, width=16, default="", show=None):
            ttk.Label(frame, text=label).grid(row=row, column=col * 2, sticky="w", padx=4, pady=2)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(frame, textvariable=var, width=width, show=show or "")
            entry.grid(row=row, column=col * 2 + 1, sticky="w", padx=4, pady=2)
            return var

        self.var_broker = add_field(0, 0, "Broker", default="localhost")
        self.var_port = add_field(0, 1, "Port", width=8, default="1883")
        ttk.Label(frame, text="MQTT Version").grid(row=0, column=4, sticky="w", padx=4)
        self.var_version = tk.StringVar(value="3.1.1")
        ttk.Combobox(
            frame, textvariable=self.var_version, values=["3.1.1", "5"], width=6, state="readonly"
        ).grid(row=0, column=5, sticky="w", padx=4)

        self.var_username = add_field(1, 0, "Username", default="")
        self.var_password = add_field(1, 1, "Password", default="", show="*")
        self.var_topic = add_field(1, 2, "Subscription Topic", width=24, default="#")

        self.var_tls = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="TLS", variable=self.var_tls, command=self._toggle_tls).grid(
            row=2, column=0, sticky="w", padx=4
        )
        self.var_ca = add_field(2, 1, "CA Certificate", width=30, default="")
        self.var_cert = add_field(2, 2, "Client Certificate", width=30, default="")
        self.var_key = add_field(2, 3, "Client Key", width=30, default="")
        self.tls_entries_row = 2

        self.btn_connect = ttk.Button(frame, text="CONNECT", command=self._on_connect)
        self.btn_connect.grid(row=0, column=6, rowspan=1, padx=8)
        self.btn_disconnect = ttk.Button(
            frame, text="DISCONNECT", command=self._on_disconnect, state="disabled"
        )
        self.btn_disconnect.grid(row=1, column=6, padx=8)

        # Optional device metadata (all None/unknown until user fills in or
        # profile is confirmed against documentation — spec section 2/12).
        meta = ttk.LabelFrame(self.root, text="Device Info (optional, for the exported profile)")
        meta.pack(fill="x", padx=6, pady=2)
        self.var_device_name = self._add_meta_field(meta, 0, "Name")
        self.var_device_model = self._add_meta_field(meta, 1, "Model")
        self.var_device_firmware = self._add_meta_field(meta, 2, "Firmware")

    def _add_meta_field(self, frame, col, label):
        ttk.Label(frame, text=label).grid(row=0, column=col * 2, sticky="w", padx=4, pady=2)
        var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=var, width=20).grid(row=0, column=col * 2 + 1, sticky="w", padx=4)
        return var

    def _toggle_tls(self) -> None:
        pass  # entries are always visible/editable; TLS checkbox just gates usage

    def _build_control_frame(self) -> None:
        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=6, pady=4)

        ttk.Button(frame, text="CLEAR", command=self._on_clear).pack(side="left", padx=2)
        self.btn_start_capture = ttk.Button(frame, text="START CAPTURE", command=self._on_start_capture)
        self.btn_start_capture.pack(side="left", padx=2)
        self.btn_stop_capture = ttk.Button(
            frame, text="STOP CAPTURE", command=self._on_stop_capture, state="disabled"
        )
        self.btn_stop_capture.pack(side="left", padx=2)
        ttk.Button(frame, text="SAVE CAPTURE", command=self._on_save_capture).pack(side="left", padx=2)
        ttk.Button(frame, text="EXPORT DEVICE PROFILE", command=self._on_export_profile).pack(
            side="left", padx=2
        )

        ttk.Label(frame, text="   Mark event:").pack(side="left", padx=(20, 2))
        self.var_event_type = tk.StringVar(value=EVENT_TYPES[0])
        ttk.Combobox(
            frame, textvariable=self.var_event_type, values=EVENT_TYPES, width=18, state="readonly"
        ).pack(side="left", padx=2)
        self.var_event_desc = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.var_event_desc, width=24).pack(side="left", padx=2)
        ttk.Button(frame, text="MARK EVENT", command=self._on_mark_event).pack(side="left", padx=2)

    def _build_notebook(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=4)

        self._build_messages_tab()
        self._build_topics_tab()
        self._build_fields_tab()
        self._build_events_tab()

    def _build_messages_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Messages")

        columns = ("time", "topic", "qos", "retain", "size", "json")
        self.tree_messages = ttk.Treeview(tab, columns=columns, show="headings", height=12)
        for col, width in zip(columns, (170, 320, 40, 60, 70, 60)):
            self.tree_messages.heading(col, text=col.upper())
            self.tree_messages.column(col, width=width, anchor="w")
        self.tree_messages.pack(fill="both", expand=True, side="top")
        self.tree_messages.bind("<<TreeviewSelect>>", self._on_select_message)

        payload_frame = ttk.Frame(tab)
        payload_frame.pack(fill="both", expand=True, side="bottom")
        ttk.Label(payload_frame, text="Raw payload:").pack(anchor="w")
        self.txt_raw = scrolledtext.ScrolledText(payload_frame, height=6)
        self.txt_raw.pack(fill="both", expand=True)
        ttk.Label(payload_frame, text="Prettified JSON:").pack(anchor="w")
        self.txt_pretty = scrolledtext.ScrolledText(payload_frame, height=8)
        self.txt_pretty.pack(fill="both", expand=True)

        self._message_index: dict[str, MessageRecord] = {}

    def _build_topics_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Topics")
        columns = ("topic", "count", "first_seen", "last_seen", "qos", "retain", "size")
        self.tree_topics = ttk.Treeview(tab, columns=columns, show="headings")
        for col, width in zip(columns, (360, 60, 170, 170, 40, 60, 60)):
            self.tree_topics.heading(col, text=col.upper())
            self.tree_topics.column(col, width=width, anchor="w")
        self.tree_topics.pack(fill="both", expand=True)

    def _build_fields_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Fields / Sensitivity Candidates")
        columns = ("topic", "json_path", "data_type", "sample", "count", "first_seen", "last_seen", "candidate")
        self.tree_fields = ttk.Treeview(tab, columns=columns, show="headings")
        for col, width in zip(columns, (220, 220, 80, 140, 60, 160, 160, 90)):
            self.tree_fields.heading(col, text=col.upper())
            self.tree_fields.column(col, width=width, anchor="w")
        self.tree_fields.tag_configure("candidate", background="#fff3cd")
        self.tree_fields.pack(fill="both", expand=True)

    def _build_events_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Events")
        columns = ("timestamp", "event_type", "description")
        self.tree_events = ttk.Treeview(tab, columns=columns, show="headings")
        for col, width in zip(columns, (200, 180, 400)):
            self.tree_events.heading(col, text=col.upper())
            self.tree_events.column(col, width=width, anchor="w")
        self.tree_events.pack(fill="both", expand=True)

    def _build_status_bar(self) -> None:
        self.status_var = tk.StringVar(value="Disconnected")
        bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        bar.pack(fill="x", side="bottom")

    # ------------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------------

    def _on_connect(self) -> None:
        try:
            port = int(self.var_port.get())
        except ValueError:
            messagebox.showerror("Invalid port", "Port must be a number")
            return

        config = MqttProbeConfig(
            broker_host=self.var_broker.get().strip(),
            broker_port=port,
            protocol_version=self.var_version.get(),
            username=self.var_username.get() or None,
            password=self.var_password.get() or None,
            tls_enabled=self.var_tls.get(),
            ca_certificate=self.var_ca.get() or None,
            client_certificate=self.var_cert.get() or None,
            client_key=self.var_key.get() or None,
            subscription_topic=self.var_topic.get().strip() or "#",
        )
        if not config.broker_host:
            messagebox.showerror("Missing broker", "Broker host is required")
            return

        connection_id = f"{config.broker_host}:{config.broker_port}"
        self.mqtt_client = ProbeMqttClient(config, connection_id=connection_id)
        self.mqtt_client.connect()
        self.btn_connect.config(state="disabled")
        self.btn_disconnect.config(state="normal")

    def _on_disconnect(self) -> None:
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        self.btn_connect.config(state="normal")
        self.btn_disconnect.config(state="disabled")

    # ------------------------------------------------------------------
    # Polling loop — the ONLY place that touches widgets from queued data
    # ------------------------------------------------------------------

    def _poll(self) -> None:
        try:
            self._poll_status()
            self._poll_messages()
        except Exception:
            # A GUI tool must never die mid-session; surface but keep running.
            traceback.print_exc()
        finally:
            self.root.after(POLL_INTERVAL_MS, self._poll)

    def _poll_status(self) -> None:
        if not self.mqtt_client:
            return
        status = self.mqtt_client.get_status()
        text = f"[{status.state.value}] {status.detail}"
        if status.last_error:
            text += f"  |  ERROR: {status.last_error}"
        self.status_var.set(text)
        if status.state == ConnectionState.ERROR:
            self.btn_connect.config(state="normal")
            self.btn_disconnect.config(state="disabled")

    def _poll_messages(self) -> None:
        if not self.mqtt_client:
            return
        for msg in self.mqtt_client.drain_messages():
            analysis = self.registry.ingest(msg)
            self._append_message_row(msg, analysis)
            self._refresh_topics()
            self._refresh_fields()
            if self.capture_active and self.capture_path:
                append_capture(self.capture_path, msg)

    # ------------------------------------------------------------------
    # Table refreshes
    # ------------------------------------------------------------------

    def _append_message_row(self, msg: MessageRecord, analysis: dict) -> None:
        size = len(msg.payload.encode("utf-8", errors="replace"))
        item_id = self.tree_messages.insert(
            "",
            "end",
            values=(msg.timestamp, msg.topic, msg.qos, msg.retain, size, "yes" if analysis["is_json"] else "no"),
        )
        self._message_index[item_id] = msg

        children = self.tree_messages.get_children()
        if len(children) > MAX_VISIBLE_MESSAGES:
            oldest = children[0]
            self.tree_messages.delete(oldest)
            self._message_index.pop(oldest, None)

        self.tree_messages.see(item_id)

    def _refresh_topics(self) -> None:
        self.tree_topics.delete(*self.tree_topics.get_children())
        for t in self.registry.topic_list():
            self.tree_topics.insert(
                "",
                "end",
                values=(t.topic, t.count, t.first_seen, t.last_seen, t.last_qos, t.last_retain, t.last_payload_size),
            )

    def _refresh_fields(self) -> None:
        self.tree_fields.delete(*self.tree_fields.get_children())
        for f in self.registry.field_list():
            tags = ("candidate",) if f.is_sensitivity_candidate else ()
            self.tree_fields.insert(
                "",
                "end",
                values=(
                    f.topic,
                    f.json_path,
                    f.data_type,
                    str(f.sample_value)[:60],
                    f.occurrence_count,
                    f.first_seen,
                    f.last_seen,
                    "POSSIBLE CANDIDATE" if f.is_sensitivity_candidate else "",
                ),
                tags=tags,
            )

    def _refresh_events(self) -> None:
        self.tree_events.delete(*self.tree_events.get_children())
        for e in self.registry.events:
            self.tree_events.insert("", "end", values=(e.timestamp, e.event_type, e.description))

    def _on_select_message(self, _event) -> None:
        selection = self.tree_messages.selection()
        if not selection:
            return
        msg = self._message_index.get(selection[0])
        if not msg:
            return
        self._selected_message = msg
        self.txt_raw.delete("1.0", tk.END)
        self.txt_raw.insert(tk.END, msg.payload)

        self.txt_pretty.delete("1.0", tk.END)
        try:
            decoded = json.loads(msg.payload)
            self.txt_pretty.insert(tk.END, json.dumps(decoded, indent=2, ensure_ascii=False))
        except (json.JSONDecodeError, TypeError, ValueError):
            self.txt_pretty.insert(tk.END, "(not valid JSON)")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_clear(self) -> None:
        if not messagebox.askyesno("Clear", "Clear all captured messages, topics and fields from memory?"):
            return
        self.registry.reset()
        self.tree_messages.delete(*self.tree_messages.get_children())
        self._message_index.clear()
        self.tree_topics.delete(*self.tree_topics.get_children())
        self.tree_fields.delete(*self.tree_fields.get_children())
        self.txt_raw.delete("1.0", tk.END)
        self.txt_pretty.delete("1.0", tk.END)

    def _on_start_capture(self) -> None:
        captures_dir = Path.cwd() / "captures"
        captures_dir.mkdir(exist_ok=True)
        self.capture_path = captures_dir / capture_filename()
        self.capture_path.touch()
        self.capture_active = True
        self.btn_start_capture.config(state="disabled")
        self.btn_stop_capture.config(state="normal")
        messagebox.showinfo("Capture started", f"Writing to {self.capture_path}")

    def _on_stop_capture(self) -> None:
        self.capture_active = False
        self.btn_start_capture.config(state="normal")
        self.btn_stop_capture.config(state="disabled")

    def _on_save_capture(self) -> None:
        if not self.registry.messages:
            messagebox.showwarning("Nothing to save", "No messages captured yet.")
            return
        default_name = capture_filename()
        path_str = filedialog.asksaveasfilename(
            defaultextension=".jsonl",
            initialfile=default_name,
            filetypes=[("JSON Lines", "*.jsonl"), ("All files", "*.*")],
        )
        if not path_str:
            return
        write_capture(Path(path_str), self.registry.messages)
        messagebox.showinfo("Saved", f"Saved {len(self.registry.messages)} messages to {path_str}")

    def _on_mark_event(self) -> None:
        event_type = self.var_event_type.get()
        description = self.var_event_desc.get()
        self.registry.mark_event(event_type, description)
        self._refresh_events()
        self.var_event_desc.set("")

    def _on_export_profile(self) -> None:
        profile = build_device_profile(
            device_name=self.var_device_name.get() or None,
            model=self.var_device_model.get() or None,
            firmware=self.var_device_firmware.get() or None,
            broker=self.var_broker.get() or None,
            port=int(self.var_port.get()) if self.var_port.get().isdigit() else None,
            protocol=self.var_version.get() or None,
            subscription=self.var_topic.get() or None,
            topics=self.registry.topic_list(),
            fields=self.registry.field_list(),
            events=self.registry.events,
            capture_file=str(self.capture_path) if self.capture_path else None,
        )
        path_str = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="device_profile.json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not path_str:
            return
        save_device_profile(Path(path_str), profile)
        messagebox.showinfo(
            "Exported",
            f"Device profile exported to {path_str}\n\n"
            f"{len(profile['variables'])} variables discovered, "
            f"{sum(1 for v in profile['variables'] if v['sensitivity_candidate'])} flagged as "
            "sensitivity candidates (all status=DISCOVERED, unconfirmed).",
        )

    def _on_close(self) -> None:
        if self.mqtt_client:
            try:
                self.mqtt_client.disconnect()
            except Exception:
                pass
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    ProbeApp(root)
    root.mainloop()
