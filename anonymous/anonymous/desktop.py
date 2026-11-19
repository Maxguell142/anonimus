"""Customizable native desktop dashboard for Anonymous."""

from __future__ import annotations

import queue
import random
import threading
import time
from typing import Any, Dict, Optional, Tuple

import psutil

from anonymous.config import USER_DATA_DIR
from anonymous.core.dispatcher import dispatcher
from anonymous.core.os_adapter import os_adapter
from anonymous.core.session import session_manager
from anonymous.desktop_layout import (
    DEFAULT_LAYOUT,
    PANEL_SPECS,
    load_layout,
    load_visible_panels,
    move_panel,
    resize_panel,
    save_layout,
)
from anonymous.engines.red.ptt import ptt_engine
from anonymous.settings import (
    BACKEND_LABELS,
    PROVIDER_LABELS,
    SettingsError,
    apply_runtime_settings,
    settings_store,
)

BACKGROUND = "#080d12"
PANEL = "#10191c"
PANEL_DARK = "#050a0d"
SURFACE = "#172326"
TEXT = "#c6d4d0"
MUTED = "#738783"
GREEN = "#9eff6e"
CYAN = "#73e8c5"
ORANGE = "#ffae57"
LAYOUT_PATH = USER_DATA_DIR / "desktop_layout.json"

MODE_CONFIG: Dict[str, Dict[str, Any]] = {
    "normal": {
        "label": "NORMAL",
        "title": "ANONYMOUS // CENTRO DE CONTROL",
        "accent": "#73e8c5",
        "event_color": "#73e8c5",
        "event": "Modo normal activo.",
        "alert": False,
    },
    "attack": {
        "label": "ATAQUE",
        "title": "SISTEMA OFENSIVO // ENLACE TÁCTICO",
        "accent": "#bd83ff",
        "event_color": "#bd83ff",
        "event": "Modo de auditoría ofensiva activado. Usa solo objetivos autorizados.",
        "alert": False,
    },
    "defense": {
        "label": "DEFENSA",
        "title": "PROTOCOLOS DE DEFENSA ACTIVADOS",
        "accent": "#ff5964",
        "event_color": "#ff5964",
        "event": "ALERTA: protocolos defensivos y monitoreo activados.",
        "alert": True,
    },
    "success": {
        "label": "ÉXITO",
        "title": "TAREA COMPLETADA CON ÉXITO",
        "accent": "#9eff6e",
        "event_color": "#9eff6e",
        "event": "TAREA COMPLETADA correctamente.",
        "alert": False,
    },
    "error": {
        "label": "ERROR",
        "title": "ERROR CRÍTICO // FALLO EN SISTEMA",
        "accent": "#ff654f",
        "event_color": "#ff654f",
        "event": "ERROR CRÍTICO: revisa el registro y el estado del sistema.",
        "alert": True,
    },
}

MATRIX_CHARS = "01アイウエオカキクケコサシスセソタチツテト"


class DesktopApp:
    """A btop/cmatrix/pipes.sh-inspired dashboard with movable, resizable panels."""

    def __init__(
        self,
        root: Any,
        tk: Any,
        ttk: Any,
        scrolled_text: Any,
        messagebox: Any,
        profile_name: str = "",
    ):
        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.scrolled_text = scrolled_text
        self.messagebox = messagebox
        self.profile_name = profile_name
        self.results: queue.Queue[Tuple[str, Any]] = queue.Queue()
        self.busy = False
        self.pending_confirmation: Optional[str] = None
        self.current_mode = "normal"
        self.mode_buttons: Dict[str, Any] = {}
        self.panel_frames: Dict[str, Any] = {}
        self.panel_items: Dict[str, int] = {}
        self.panel_controls: Dict[str, Any] = {}
        self.panel_title_labels: Dict[str, Any] = {}
        self.visible_panels = load_visible_panels(LAYOUT_PATH)
        self.layout = load_layout(LAYOUT_PATH)
        self.drag_state: Optional[Tuple[str, int, int]] = None
        self.resize_state: Optional[Tuple[str, int, int, int, int]] = None
        self._animation_jobs: list[Any] = []
        psutil.cpu_percent(interval=None)

        root.title("Anonymous | Centro de Control")
        root.geometry("1500x940")
        root.minsize(980, 680)
        root.configure(background=BACKGROUND)
        root.protocol("WM_DELETE_WINDOW", self._close)
        self._build_layout()
        self.set_mode("normal", add_event=False)
        self._append_event("ANONYMOUS", "Centro de control iniciado.", MUTED)
        if self.profile_name:
            self._append_event("PERFIL", f"Sesión local de {self.profile_name}.", MUTED, "muted")
        self._refresh_panels()
        self._animate_matrix()
        self._animate_pipes()
        root.after(100, self._process_results)
        root.after(1500, self._update_system_metrics)

    def _build_layout(self) -> None:
        tk = self.tk
        self.root.configure(background=BACKGROUND)
        shell = tk.Frame(self.root, bg=BACKGROUND)
        shell.pack(fill="both", expand=True, padx=12, pady=10)

        top = tk.Frame(shell, bg=PANEL, padx=14, pady=8)
        top.pack(fill="x")
        tk.Label(
            top,
            text="ANONYMOUS",
            bg=PANEL,
            fg=CYAN,
            font=("Cascadia Code", 17, "bold"),
        ).pack(side="left")
        self.hero_title = tk.Label(
            top,
            text=MODE_CONFIG["normal"]["title"],
            bg=PANEL,
            fg=TEXT,
            font=("Cascadia Code", 10, "bold"),
        )
        self.hero_title.pack(side="left", padx=20)
        self.status_label = tk.Label(
            top,
            text="INICIANDO…",
            bg=PANEL,
            fg=GREEN,
            font=("Cascadia Code", 8, "bold"),
        )
        self.status_label.pack(side="right")

        toolbar = tk.Frame(shell, bg=PANEL, padx=10, pady=6)
        toolbar.pack(fill="x", pady=(5, 8))
        for mode, config in MODE_CONFIG.items():
            button = tk.Button(
                toolbar,
                text=config["label"],
                command=lambda selected=mode: self.set_mode(selected),
                bg=SURFACE,
                fg=TEXT,
                activebackground=config["accent"],
                activeforeground=BACKGROUND,
                relief="flat",
                borderwidth=0,
                padx=11,
                pady=6,
                font=("Cascadia Code", 8, "bold"),
                cursor="hand2",
            )
            button.pack(side="left", padx=3)
            self.mode_buttons[mode] = button

        tk.Label(
            toolbar,
            text="PANELES",
            bg=PANEL,
            fg=MUTED,
            font=("Cascadia Code", 8, "bold"),
        ).pack(side="left", padx=(15, 4))
        for panel_id, spec in PANEL_SPECS.items():
            button = tk.Button(
                toolbar,
                text=panel_id.upper(),
                command=lambda selected=panel_id: self.toggle_panel(selected),
                bg=SURFACE,
                fg=TEXT,
                relief="flat",
                borderwidth=0,
                padx=7,
                pady=5,
                font=("Cascadia Code", 7, "bold"),
                cursor="hand2",
            )
            button.pack(side="left", padx=2)
            self.panel_controls[panel_id] = button
        tk.Button(
            toolbar,
            text="RESTABLECER DISTRIBUCIÓN",
            command=self.reset_layout,
            bg=SURFACE,
            fg=MUTED,
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=5,
            font=("Cascadia Code", 7, "bold"),
            cursor="hand2",
        ).pack(side="right", padx=3)
        tk.Button(
            toolbar,
            text="CONFIGURACIÓN",
            command=self._open_settings_dialog,
            bg=SURFACE,
            fg=CYAN,
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=5,
            font=("Cascadia Code", 7, "bold"),
            cursor="hand2",
        ).pack(side="right", padx=3)

        workspace_frame = tk.Frame(shell, bg=BACKGROUND)
        workspace_frame.pack(fill="both", expand=True)
        workspace_frame.rowconfigure(0, weight=1)
        workspace_frame.columnconfigure(0, weight=1)
        self.workspace = tk.Canvas(workspace_frame, bg=BACKGROUND, highlightthickness=0)
        vertical = tk.Scrollbar(workspace_frame, orient="vertical", command=self.workspace.yview)
        horizontal = tk.Scrollbar(workspace_frame, orient="horizontal", command=self.workspace.xview)
        self.workspace.configure(
            xscrollcommand=horizontal.set,
            yscrollcommand=vertical.set,
        )
        self.workspace.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.workspace.bind("<Configure>", self._on_workspace_resize)
        self.workspace.bind_all("<MouseWheel>", self._on_mousewheel)
        self._create_panels()

        self.footer_label = tk.Label(
            shell,
            text="ANONYMOUS // arrastra los títulos para mover · esquina inferior derecha para redimensionar · oculta/muestra desde PANELES",
            bg=BACKGROUND,
            fg=MUTED,
            font=("Cascadia Code", 8),
            anchor="w",
        )
        self.footer_label.pack(fill="x", pady=(5, 0))

    def _create_panels(self) -> None:
        for panel_id in PANEL_SPECS:
            frame = self.tk.Frame(
                self.workspace,
                bg=PANEL,
                highlightthickness=1,
                highlightbackground="#2c3d3b",
            )
            self.panel_frames[panel_id] = frame
            self._build_panel(panel_id, frame)
            x, y, width, height = self.layout[panel_id]
            item = self.workspace.create_window(
                x,
                y,
                window=frame,
                width=width,
                height=height,
                anchor="nw",
                tags=("panel", f"panel:{panel_id}"),
            )
            self.panel_items[panel_id] = item
            self._bind_panel_drag(panel_id, frame)
            if panel_id not in self.visible_panels:
                self.workspace.itemconfigure(item, state="hidden")

    def _build_panel(self, panel_id: str, frame: Any) -> None:
        tk = self.tk
        spec = PANEL_SPECS[panel_id]
        header = tk.Frame(frame, bg="#172426", padx=8, pady=5, cursor="fleur")
        header.pack(fill="x")
        title_label = tk.Label(
            header,
            text=spec["title"],
            bg="#172426",
            fg=self.current_accent,
            font=("Cascadia Code", 8, "bold"),
            anchor="w",
        )
        title_label.pack(side="left", fill="x", expand=True)
        self.panel_title_labels[panel_id] = title_label
        close = tk.Button(
            header,
            text="×",
            command=lambda selected=panel_id: self.toggle_panel(selected, visible=False),
            bg="#172426",
            fg=MUTED,
            activebackground="#263538",
            relief="flat",
            borderwidth=0,
            padx=5,
            font=("Cascadia Code", 10, "bold"),
        )
        close.pack(side="right")
        body = tk.Frame(frame, bg=PANEL, padx=9, pady=7)
        body.pack(fill="both", expand=True)
        self._bind_panel_drag(panel_id, header)
        self._bind_panel_drag(panel_id, header.winfo_children()[0])

        if panel_id == "system":
            self._build_system_panel(body)
        elif panel_id == "matrix":
            self.matrix_canvas = tk.Canvas(body, bg=PANEL_DARK, highlightthickness=0)
            self.matrix_canvas.pack(fill="both", expand=True)
        elif panel_id == "pipes":
            self.pipes_canvas = tk.Canvas(body, bg=PANEL_DARK, highlightthickness=0)
            self.pipes_canvas.pack(fill="both", expand=True)
        elif panel_id == "events":
            self.event_log = tk.Text(
                body,
                wrap="word",
                state="disabled",
                bg=PANEL_DARK,
                fg=TEXT,
                insertbackground=TEXT,
                relief="flat",
                font=("Cascadia Code", 8),
                padx=8,
                pady=8,
            )
            self.event_log.pack(fill="both", expand=True)
            self.event_log.tag_configure("muted", foreground=MUTED)
            self.event_log.tag_configure("alert", foreground="#ff5964")
            self.event_log.tag_configure("success", foreground=GREEN)
            self.event_log.tag_configure("normal", foreground=CYAN)
            self.event_log.tag_configure("command", foreground="#bd83ff")
        elif panel_id == "assistant":
            self._build_assistant_panel(body)
        elif panel_id == "findings":
            self.findings_output = tk.Text(
                body,
                wrap="word",
                state="disabled",
                bg=PANEL_DARK,
                fg=TEXT,
                relief="flat",
                font=("Cascadia Code", 8),
                padx=8,
                pady=7,
            )
            self.findings_output.pack(fill="both", expand=True)
        self._add_resize_handle(panel_id, frame)

    def _build_system_panel(self, parent: Any) -> None:
        tk = self.tk
        self.metric_bars: Dict[str, Tuple[Any, Any]] = {}
        for key, title in (("cpu", "CPU"), ("memory", "MEMORIA"), ("disk", "DISCO")):
            row = tk.Frame(parent, bg=PANEL)
            row.pack(fill="x", pady=5)
            header = tk.Frame(row, bg=PANEL)
            header.pack(fill="x")
            tk.Label(
                header,
                text=title,
                bg=PANEL,
                fg=TEXT,
                font=("Cascadia Code", 8, "bold"),
            ).pack(side="left")
            value = tk.Label(
                header,
                text="--%",
                bg=PANEL,
                fg=self.current_accent,
                font=("Cascadia Code", 8, "bold"),
            )
            value.pack(side="right")
            track = tk.Canvas(row, height=8, bg="#253432", highlightthickness=0)
            track.pack(fill="x", pady=(4, 0))
            self.metric_bars[key] = (track, value)
        self.network_label = tk.Label(
            parent,
            text="NET RX 0 B/s   TX 0 B/s",
            bg=PANEL,
            fg=MUTED,
            font=("Cascadia Code", 8),
            anchor="w",
        )
        self.network_label.pack(fill="x", pady=(8, 3))
        self.machine_label = tk.Label(
            parent,
            text="SISTEMA · detectando",
            bg=PANEL,
            fg=MUTED,
            font=("Cascadia Code", 8),
            anchor="w",
        )
        self.machine_label.pack(fill="x")

    def _build_assistant_panel(self, parent: Any) -> None:
        tk = self.tk
        self.assistant_output = tk.Text(
            parent,
            wrap="word",
            state="disabled",
            bg=PANEL_DARK,
            fg=TEXT,
            relief="flat",
            font=("Cascadia Code", 8),
            padx=8,
            pady=7,
            height=6,
        )
        self.assistant_output.pack(fill="both", expand=True, pady=(0, 7))
        command_row = tk.Frame(parent, bg=PANEL)
        command_row.pack(fill="x")
        command_row.columnconfigure(0, weight=1)
        self.command_entry = tk.Entry(
            command_row,
            bg=PANEL_DARK,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Cascadia Code", 9),
        )
        self.command_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=6)
        self.command_entry.bind("<Return>", lambda _event: self._submit_from_entry())
        self.send_button = tk.Button(
            command_row,
            text="RUN",
            command=self._submit_from_entry,
            bg=self.current_accent,
            fg=BACKGROUND,
            relief="flat",
            padx=10,
            pady=5,
            font=("Cascadia Code", 8, "bold"),
        )
        self.send_button.grid(row=0, column=1)

    def _add_resize_handle(self, panel_id: str, frame: Any) -> None:
        handle = self.tk.Label(
            frame,
            text="◢",
            bg=PANEL,
            fg=MUTED,
            cursor="size_nw_se",
            font=("Segoe UI", 9),
        )
        handle.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-1)
        handle.bind(
            "<ButtonPress-1>",
            lambda event, selected=panel_id: self._start_resize(selected, event),
        )
        handle.bind("<B1-Motion>", self._continue_resize)
        handle.bind("<ButtonRelease-1>", lambda _event: self._finish_panel_edit())

    def _bind_panel_drag(self, panel_id: str, widget: Any) -> None:
        widget.bind(
            "<ButtonPress-1>",
            lambda event, selected=panel_id: self._start_drag(selected, event),
        )
        widget.bind("<B1-Motion>", self._continue_drag)
        widget.bind("<ButtonRelease-1>", lambda _event: self._finish_panel_edit())

    def _start_drag(self, panel_id: str, event: Any) -> None:
        self.drag_state = (panel_id, event.x_root, event.y_root)

    def _continue_drag(self, event: Any) -> None:
        if not self.drag_state:
            return
        panel_id, previous_x, previous_y = self.drag_state
        dx, dy = event.x_root - previous_x, event.y_root - previous_y
        x, y, width, height = self.layout[panel_id]
        self.layout = move_panel(self.layout, panel_id, x + dx, y + dy)
        self.workspace.coords(self.panel_items[panel_id], x + dx, y + dy)
        self.drag_state = (panel_id, event.x_root, event.y_root)

    def _start_resize(self, panel_id: str, event: Any) -> None:
        x, y, width, height = self.layout[panel_id]
        self.resize_state = (panel_id, event.x_root, event.y_root, width, height)

    def _continue_resize(self, event: Any) -> None:
        if not self.resize_state:
            return
        panel_id, start_x, start_y, start_width, start_height = self.resize_state
        width = max(
            PANEL_SPECS[panel_id]["min_width"],
            start_width + event.x_root - start_x,
        )
        height = max(
            PANEL_SPECS[panel_id]["min_height"],
            start_height + event.y_root - start_y,
        )
        self.layout = resize_panel(self.layout, panel_id, width, height)
        self.workspace.itemconfigure(self.panel_items[panel_id], width=width, height=height)

    def _finish_panel_edit(self) -> None:
        self.drag_state = None
        self.resize_state = None
        self.workspace.configure(scrollregion=self.workspace.bbox("all"))
        self._persist_layout()

    def _on_workspace_resize(self, _event: Any) -> None:
        self.workspace.configure(scrollregion=self.workspace.bbox("all"))

    def _on_mousewheel(self, event: Any) -> None:
        if event.state & 0x0001:
            self.workspace.xview_scroll(int(-event.delta / 120), "units")
        elif self.workspace.winfo_containing(event.x_root, event.y_root) == self.workspace:
            self.workspace.yview_scroll(int(-event.delta / 120), "units")

    def toggle_panel(self, panel_id: str, visible: Optional[bool] = None) -> None:
        if panel_id not in PANEL_SPECS:
            raise KeyError(f"Unknown panel: {panel_id}")
        if visible is None:
            visible = panel_id not in self.visible_panels
        if visible:
            self.visible_panels.add(panel_id)
            self.workspace.itemconfigure(self.panel_items[panel_id], state="normal")
            x, y, _width, _height = self.layout[panel_id]
            self.workspace.coords(self.panel_items[panel_id], x, y)
        else:
            self.visible_panels.discard(panel_id)
            self.workspace.itemconfigure(self.panel_items[panel_id], state="hidden")
        self._persist_layout()

    def reset_layout(self) -> None:
        self.layout = dict(DEFAULT_LAYOUT)
        self.visible_panels = set(PANEL_SPECS)
        for panel_id, item in self.panel_items.items():
            x, y, width, height = self.layout[panel_id]
            self.workspace.coords(item, x, y)
            self.workspace.itemconfigure(item, width=width, height=height, state="normal")
        self._persist_layout()

    def _persist_layout(self) -> None:
        save_layout(LAYOUT_PATH, self.layout, self.visible_panels)

    def _open_settings_dialog(self) -> None:
        try:
            settings = settings_store.load()
        except SettingsError as exc:
            self.messagebox.showerror(
                "Configuración no disponible",
                f"No se pudieron leer los ajustes:\n{exc}",
                parent=self.root,
            )
            return
        dialog = self.tk.Toplevel(self.root)
        dialog.title("Anonymous | Configuración")
        dialog.geometry("760x850")
        dialog.minsize(650, 700)
        dialog.transient(self.root)
        dialog.grab_set()

        content = self.ttk.Frame(dialog, padding=12)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)

        ai_frame = self.ttk.LabelFrame(content, text="Inteligencia artificial", padding=10)
        ai_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ai_frame.columnconfigure(1, weight=1)
        provider_display_by_key = {
            key: label for key, label in PROVIDER_LABELS.items()
        }
        provider_key_by_display = {
            label: key for key, label in PROVIDER_LABELS.items()
        }
        provider_var = self.tk.StringVar(value=provider_display_by_key[settings["ai_provider"]])
        self.ttk.Label(ai_frame, text="Proveedor").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=3)
        self.ttk.Combobox(
            ai_frame,
            textvariable=provider_var,
            values=tuple(PROVIDER_LABELS.values()),
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=3)

        entries: Dict[str, Any] = {}

        def add_entry(parent: Any, row: int, label: str, key: str, value: Any, secret: bool = False) -> Any:
            self.ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=3)
            entry = self.ttk.Entry(parent, show="*" if secret else "")
            entry.insert(0, str(value))
            entry.grid(row=row, column=1, sticky="ew", pady=3)
            entries[key] = entry
            return entry

        add_entry(ai_frame, 1, "URL Ollama", "ollama_base_url", settings["ollama_base_url"])
        add_entry(ai_frame, 2, "Modelo Ollama", "ollama_model", settings["ollama_model"])
        add_entry(ai_frame, 3, "Modelo Gemini", "gemini_model", settings["gemini_model"])
        add_entry(
            ai_frame,
            4,
            "Modelo Gemini de respaldo",
            "gemini_fallback_model",
            settings["gemini_fallback_model"],
        )
        add_entry(ai_frame, 5, "Timeout Ollama (s)", "ollama_timeout", settings["ollama_timeout"])
        add_entry(ai_frame, 6, "Timeout Gemini (s)", "gemini_timeout", settings["gemini_timeout"])
        try:
            key_status = "configurada" if settings_store.get_api_key() else "no configurada"
        except SettingsError as exc:
            key_status = f"no disponible ({exc})"
        self.ttk.Label(
            ai_frame,
            text=(
                f"Clave API Gemini: {key_status} (nunca se muestra ni se guarda en settings.json; "
                "si no hay clave de sistema, se usa GEMINI_API_KEY)"
            ),
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(5, 2))
        key_entry = self.ttk.Entry(ai_frame, show="*")
        key_entry.grid(row=8, column=1, sticky="ew", pady=3)
        self.ttk.Label(ai_frame, text="Nueva clave API Gemini").grid(row=8, column=0, sticky="w", padx=(0, 10), pady=3)
        clear_key_var = self.tk.BooleanVar(value=False)
        self.ttk.Checkbutton(
            ai_frame,
            text="Eliminar la clave del almacén del sistema (no borra GEMINI_API_KEY)",
            variable=clear_key_var,
        ).grid(row=9, column=0, columnspan=2, sticky="w", pady=(3, 0))

        environment_frame = self.ttk.LabelFrame(content, text="Entorno Kali y conexión", padding=10)
        environment_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        environment_frame.columnconfigure(1, weight=1)
        backend_display_by_key = {key: label for key, label in BACKEND_LABELS.items()}
        backend_key_by_display = {label: key for key, label in BACKEND_LABELS.items()}
        backend_var = self.tk.StringVar(value=backend_display_by_key[settings["kali_backend"]])
        self.ttk.Label(environment_frame, text="Entorno").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=3
        )
        self.ttk.Combobox(
            environment_frame,
            textvariable=backend_var,
            values=tuple(BACKEND_LABELS.values()),
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=3)
        self.ttk.Label(
            environment_frame,
            text=(
                "native = motores locales; docker y VirtualBox usan MCP; cloud conecta al Kali existente "
                "por SSH con host key verificada."
            ),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(3, 5))
        for row, backend in enumerate(("docker", "virtualbox"), start=2):
            add_entry(
                environment_frame,
                row,
                f"URL MCP {backend}",
                f"mcp_{backend}",
                settings["mcp_urls"][backend],
            )
        cloud_ssh = settings["cloud_ssh"]
        add_entry(environment_frame, 4, "Host o IPv4 Kali cloud", "ssh_host", cloud_ssh["host"])
        add_entry(environment_frame, 5, "Usuario SSH", "ssh_username", cloud_ssh["username"])
        add_entry(environment_frame, 6, "Puerto SSH", "ssh_port", cloud_ssh["port"])

        from tkinter import filedialog

        def add_path_entry(row: int, label: str, key: str, value: str, title: str) -> None:
            add_entry(environment_frame, row, label, key, value)

            def browse() -> None:
                selected = filedialog.askopenfilename(parent=dialog, title=title)
                if selected:
                    entries[key].delete(0, "end")
                    entries[key].insert(0, selected)

            self.ttk.Button(
                environment_frame,
                text="Examinar...",
                command=browse,
            ).grid(row=row, column=2, padx=(6, 0), pady=3)

        add_path_entry(7, "Clave privada SSH", "ssh_key_path", cloud_ssh["key_path"], "Seleccionar clave SSH")
        add_path_entry(
            8,
            "Archivo known_hosts",
            "ssh_known_hosts",
            cloud_ssh["known_hosts"],
            "Seleccionar known_hosts",
        )

        profile_frame = self.ttk.LabelFrame(content, text="Perfil local", padding=10)
        profile_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        profile_frame.columnconfigure(1, weight=1)
        add_entry(profile_frame, 0, "Nombre visible", "user_name", settings["user_name"])
        self.ttk.Label(
            content,
            text="AgentShield y las confirmaciones de seguridad permanecen activos para todos los entornos.",
        ).grid(row=3, column=0, sticky="w", pady=(0, 8))

        buttons = self.ttk.Frame(content)
        buttons.grid(row=4, column=0, sticky="e")
        self.ttk.Button(buttons, text="Cancelar", command=dialog.destroy).pack(side="right", padx=(6, 0))

        def save_dialog_settings() -> None:
            updated = dict(settings)
            updated["ai_provider"] = provider_key_by_display[provider_var.get()]
            updated["ollama_base_url"] = entries["ollama_base_url"].get().strip()
            updated["ollama_model"] = entries["ollama_model"].get().strip()
            updated["gemini_model"] = entries["gemini_model"].get().strip()
            updated["gemini_fallback_model"] = entries["gemini_fallback_model"].get().strip()
            try:
                updated["ollama_timeout"] = int(entries["ollama_timeout"].get())
                updated["gemini_timeout"] = int(entries["gemini_timeout"].get())
            except ValueError:
                self.messagebox.showerror(
                    "Timeout no válido",
                    "Los timeouts deben ser números enteros.",
                    parent=dialog,
                )
                return
            updated["kali_backend"] = backend_key_by_display[backend_var.get()]
            updated["user_name"] = entries["user_name"].get().strip()
            updated["mcp_urls"] = {
                backend: entries[f"mcp_{backend}"].get().strip()
                for backend in ("docker", "virtualbox")
            }
            updated["mcp_urls"]["cloud"] = settings["mcp_urls"]["cloud"]
            updated["cloud_ssh"] = dict(settings["cloud_ssh"])
            updated["cloud_ssh"].update(
                host=entries["ssh_host"].get().strip(),
                username=entries["ssh_username"].get().strip(),
                key_path=entries["ssh_key_path"].get().strip(),
                known_hosts=entries["ssh_known_hosts"].get().strip(),
            )
            try:
                updated["cloud_ssh"]["port"] = int(entries["ssh_port"].get())
            except ValueError:
                self.messagebox.showerror(
                    "Puerto SSH no válido",
                    "El puerto SSH debe ser un número entero.",
                    parent=dialog,
                )
                return
            try:
                settings_store.save(updated)
            except (SettingsError, ValueError, OSError) as exc:
                self.messagebox.showerror(
                    "Ajustes no guardados",
                    f"No se guardaron los cambios:\n{exc}",
                    parent=dialog,
                )
                return

            new_key = key_entry.get()
            try:
                if clear_key_var.get():
                    settings_store.set_api_key("")
                elif new_key:
                    settings_store.set_api_key(new_key)
            except SettingsError as exc:
                try:
                    apply_runtime_settings(updated)
                except (SettingsError, ValueError, RuntimeError, OSError) as apply_exc:
                    self.messagebox.showerror(
                        "Ajustes guardados parcialmente",
                        f"Las preferencias se guardaron, pero la clave no pudo actualizarse "
                        f"y no se aplicaron en memoria:\n{exc}\n{apply_exc}",
                        parent=dialog,
                    )
                    return
                self.messagebox.showerror(
                    "Clave no actualizada",
                    f"Los demás ajustes se guardaron, pero la clave no pudo actualizarse:\n{exc}",
                    parent=dialog,
                )
                return

            try:
                apply_runtime_settings(updated)
            except (SettingsError, ValueError, RuntimeError, OSError) as exc:
                self.messagebox.showerror(
                    "Ajustes guardados parcialmente",
                    f"Se guardaron las preferencias, pero no se pudieron aplicar en memoria:\n{exc}",
                    parent=dialog,
                )
                return
            self.messagebox.showinfo(
                "Configuración",
                "Ajustes guardados y aplicados.",
                parent=dialog,
            )
            dialog.destroy()

        self.ttk.Button(buttons, text="Guardar", command=save_dialog_settings).pack(side="right")

    def set_mode(self, mode: str, add_event: bool = True) -> None:
        if mode not in MODE_CONFIG:
            raise ValueError(f"Unknown interface mode: {mode}")
        config = MODE_CONFIG[mode]
        self.current_mode = mode
        self.hero_title.configure(text=config["title"], fg=config["accent"])
        for label in self.panel_title_labels.values():
            label.configure(fg=config["accent"])
        for key, button in self.mode_buttons.items():
            selected = key == mode
            button.configure(
                bg=config["accent"] if selected else SURFACE,
                fg=BACKGROUND if selected else TEXT,
                activebackground=config["accent"],
                activeforeground=BACKGROUND,
            )
        if hasattr(self, "send_button"):
            self.send_button.configure(bg=config["accent"])
        for name in ("cpu", "memory", "disk"):
            if hasattr(self, "metric_bars") and name in self.metric_bars:
                self.metric_bars[name][1].configure(fg=config["accent"])
        if add_event:
            tag = "alert" if config["alert"] else ("success" if mode == "success" else "normal")
            self._append_event("MODO", config["event"], config["event_color"], tag)

    @property
    def current_accent(self) -> str:
        return MODE_CONFIG[self.current_mode]["accent"]

    def _animate_matrix(self) -> None:
        canvas = getattr(self, "matrix_canvas", None)
        if canvas is None:
            return
        canvas.delete("matrix")
        width, height = max(canvas.winfo_width(), 220), max(canvas.winfo_height(), 150)
        columns = max(8, width // 18)
        for _ in range(columns):
            x = random.randrange(0, width)
            y = random.randrange(0, height)
            length = random.randrange(2, 9)
            for row in range(length):
                char = random.choice(MATRIX_CHARS)
                color = GREEN if row == 0 else random.choice(("#4caf7d", "#286849", "#173a32"))
                canvas.create_text(
                    x,
                    (y + row * 15) % height,
                    text=char,
                    fill=color,
                    font=("Cascadia Code", 10, "bold"),
                    tags=("matrix",),
                )
        self._animation_jobs.append(self.root.after(240, self._animate_matrix))

    def _animate_pipes(self) -> None:
        canvas = getattr(self, "pipes_canvas", None)
        if canvas is None:
            return
        canvas.delete("pipes")
        width, height = max(canvas.winfo_width(), 200), max(canvas.winfo_height(), 140)
        cell = 16
        cols, rows = max(4, width // cell), max(4, height // cell)
        x, y = random.randrange(cols), random.randrange(rows)
        points = [(x * cell + 8, y * cell + 8)]
        direction = random.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
        for _ in range(random.randrange(8, 35)):
            if random.random() < 0.28:
                direction = random.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            x = (x + direction[0]) % cols
            y = (y + direction[1]) % rows
            points.append((x * cell + 8, y * cell + 8))
        color = random.choice((self.current_accent, GREEN, "#57bd9a"))
        for start, end in zip(points, points[1:]):
            canvas.create_line(
                *start, *end, fill=color, width=2, capstyle="round", tags=("pipes",)
            )
            canvas.create_oval(
                start[0] - 2, start[1] - 2, start[0] + 2, start[1] + 2,
                fill=color, outline="", tags=("pipes",),
            )
        self._animation_jobs.append(self.root.after(700, self._animate_pipes))

    def _update_system_metrics(self) -> None:
        try:
            cpu = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(USER_DATA_DIR))
            network = psutil.net_io_counters()
            now = time.monotonic()
            previous = getattr(self, "_network_sample", None)
            if previous is None:
                rx_rate = tx_rate = 0
            else:
                elapsed = max(now - previous[0], 0.001)
                rx_rate = (network.bytes_recv - previous[1]) / elapsed
                tx_rate = (network.bytes_sent - previous[2]) / elapsed
            self._network_sample = (now, network.bytes_recv, network.bytes_sent)
            self._set_metric("cpu", cpu, f"{cpu:.0f}%")
            self._set_metric("memory", memory.percent, f"{memory.percent:.0f}% · {memory.used / (1024**3):.1f}/{memory.total / (1024**3):.1f} GB")
            self._set_metric("disk", disk.percent, f"{disk.percent:.0f}% · {disk.free / (1024**3):.0f} GB libres")
            self.network_label.configure(text=f"NET ↓ {self._format_rate(rx_rate)}   ↑ {self._format_rate(tx_rate)}")
            info = os_adapter.get_system_info()
            self.machine_label.configure(
                text=f"{info.get('os', 'SISTEMA')} · {info.get('hostname', 'equipo')} · {psutil.cpu_count(logical=True) or '?'} hilos"
            )
            self.status_label.configure(text=f"ONLINE · CPU {cpu:.0f}% · RAM {memory.percent:.0f}%")
        except Exception as exc:
            self._append_event("MONITOR", f"No se pudieron actualizar métricas: {exc}", ORANGE, "alert")
        self.root.after(1500, self._update_system_metrics)

    def _set_metric(self, key: str, percent: float, text: str) -> None:
        canvas, label = self.metric_bars[key]
        label.configure(text=text)
        canvas.delete("bar")
        width = max(canvas.winfo_width(), 150)
        color = ORANGE if percent >= 85 else self.current_accent
        canvas.create_rectangle(
            0, 0, width * min(max(percent, 0), 100) / 100, 8,
            fill=color, outline="", tags=("bar",),
        )

    @staticmethod
    def _format_rate(rate: float) -> str:
        units = ("B/s", "KB/s", "MB/s", "GB/s")
        value = max(rate, 0.0)
        unit = units[0]
        for unit in units:
            if value < 1024 or unit == units[-1]:
                break
            value /= 1024
        return f"{value:.1f} {unit}"

    def _append_event(
        self, source: str, message: str, color: str, tag: Optional[str] = None
    ) -> None:
        if not hasattr(self, "event_log"):
            return
        self.event_log.configure(state="normal")
        event_tag = tag or "dynamic"
        self.event_log.tag_configure(event_tag, foreground=color)
        timestamp = time.strftime("%H:%M:%S")
        self.event_log.insert("end", f"[{timestamp}] {source}: {message}\n\n", event_tag)
        self.event_log.see("end")
        self.event_log.configure(state="disabled")

    def _submit_from_entry(self) -> None:
        self._submit(self.command_entry.get())

    def _submit(self, text: str, confirmed: bool = False, echo_user: bool = True) -> None:
        command = text.strip()
        if not command or self.busy:
            return
        if echo_user:
            self._append_event("COMANDO", command, self.current_accent, "command")
        self.command_entry.delete(0, "end")
        self.busy = True
        self.send_button.configure(state="disabled")
        self.status_label.configure(text="PROCESANDO…")

        def run_command() -> None:
            try:
                result = dispatcher.process_input(command, confirmed_by_user=confirmed)
                self.results.put(("command", (command, result)))
            except Exception as exc:
                self.results.put(("error", str(exc)))

        threading.Thread(target=run_command, daemon=True).start()

    def _refresh_panels(self) -> None:
        def load() -> None:
            try:
                info = os_adapter.get_system_info()
                tasks = ptt_engine.get_all_tasks()
                findings = session_manager.get_findings(limit=8)
                self.results.put(("summary", (info, tasks, findings)))
            except Exception as exc:
                self.results.put(("error", str(exc)))

        threading.Thread(target=load, daemon=True).start()

    def _process_results(self) -> None:
        while True:
            try:
                kind, payload = self.results.get_nowait()
            except queue.Empty:
                break

            if kind == "command":
                command, result = payload
                self.busy = False
                self.send_button.configure(state="normal")
                if result.get("type") == "confirmation_required":
                    self.pending_confirmation = result.get("pending_message", command)
                    approved = self.messagebox.askyesno(
                        "Confirmación requerida",
                        result.get("message", "¿Autorizar esta acción?"),
                        parent=self.root,
                    )
                    pending, self.pending_confirmation = self.pending_confirmation, None
                    if approved and pending:
                        self._submit(pending, confirmed=True, echo_user=False)
                    else:
                        self._append_event("AGENTSHIELD", "Acción cancelada.", ORANGE)
                else:
                    reply = result.get("message", "Operación procesada.")
                    self._append_output("Anonymous", reply)
                    self._append_event("RESULTADO", reply, self.current_accent)
                    self.status_label.configure(text="ONLINE")
                    self._refresh_panels()
            elif kind == "summary":
                info, tasks, findings = payload
                self.machine_label.configure(
                    text=f"{info.get('os', 'SISTEMA')} · {info.get('hostname', 'equipo')}"
                )
                self._render_findings(findings)
                self._append_event("ACTIVIDAD", f"{len(tasks)} tareas registradas · {len(findings)} hallazgos recientes.", MUTED, "muted")
            elif kind == "error":
                self.busy = False
                self.send_button.configure(state="normal")
                self.status_label.configure(text="ERROR DE OPERACIÓN")
                self.set_mode("error")
                self._append_output("ERROR", str(payload))
                self._append_event("ERROR", str(payload), MODE_CONFIG["error"]["event_color"], "alert")

        self.root.after(100, self._process_results)

    def _append_output(self, speaker: str, text: str) -> None:
        self.assistant_output.configure(state="normal")
        self.assistant_output.insert("end", f"{speaker} > {text}\n\n")
        self.assistant_output.see("end")
        self.assistant_output.configure(state="disabled")

    def _render_findings(self, findings: list[Dict[str, Any]]) -> None:
        self.findings_output.configure(state="normal")
        self.findings_output.delete("1.0", "end")
        if findings:
            for finding in findings:
                self.findings_output.insert(
                    "end",
                    f"[{finding.get('severity', 'INFO')}] {finding.get('target', '')}\n"
                    f"{finding.get('title', '')}\n{finding.get('details', '')}\n\n",
                )
        else:
            self.findings_output.insert("end", "Sin hallazgos. Ejecuta un análisis para revisar un activo propio.")
        self.findings_output.configure(state="disabled")

    def _close(self) -> None:
        self._persist_layout()
        for job in self._animation_jobs:
            try:
                self.root.after_cancel(job)
            except self.tk.TclError:
                pass
        self.root.destroy()


def run_desktop() -> None:
    """Start the native Anonymous dashboard."""
    settings = None
    settings_error = ""
    try:
        settings = apply_runtime_settings()
    except (SettingsError, ValueError, RuntimeError, OSError) as exc:
        settings_error = str(exc)
    try:
        import tkinter as tk
        from tkinter import messagebox, scrolledtext, ttk
    except ImportError as exc:
        raise RuntimeError(
            "No se encontró Tkinter. Instala una distribución de Python que incluya Tcl/Tk."
        ) from exc

    root = tk.Tk()
    DesktopApp(
        root,
        tk,
        ttk,
        scrolledtext,
        messagebox,
        profile_name=settings["user_name"] if settings else "",
    )
    if settings_error:
        root.after(
            0,
            lambda: messagebox.showerror(
                "Ajustes no aplicados",
                f"Anonymous inició con la configuración predeterminada:\n{settings_error}",
                parent=root,
            ),
        )
    root.mainloop()
