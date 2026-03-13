#!/usr/bin/env python3
"""
gui_app.py
══════════════════════════════════════════════════════════════════
Balfund Trading Pvt. Ltd.
Morning Star / Evening Star — NIFTY Options Strategy
CustomTkinter GUI  |  Dark Trading Theme
══════════════════════════════════════════════════════════════════
"""

import os
import sys
import time
import logging
import threading
import importlib
from datetime import datetime
from pathlib import Path
from typing import Optional

import pytz
import customtkinter as ctk
from dotenv import load_dotenv, set_key

# ── Appearance ────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

IST = pytz.timezone("Asia/Kolkata")
ENV_FILE = Path(".env")

# ── Palette ───────────────────────────────────────────────────
C_BG      = "#080d1a"
C_PANEL   = "#0e1525"
C_CARD    = "#111d35"
C_BORDER  = "#1e3050"
C_GREEN   = "#00c896"
C_RED     = "#ff4d6d"
C_YELLOW  = "#ffc947"
C_BLUE    = "#4a9eff"
C_PURPLE  = "#a855f7"
C_TEXT    = "#e2eaf6"
C_MUTED   = "#5a7090"
C_DARK    = "#060b16"

FONT_H1   = ("Segoe UI", 28, "bold")
FONT_H2   = ("Segoe UI", 18, "bold")
FONT_H3   = ("Segoe UI", 14, "bold")
FONT_BODY = ("Segoe UI", 13)
FONT_MONO = ("Consolas", 12)
FONT_SM   = ("Segoe UI", 11)


# ─────────────────────────────────────────────────────────────
# GUI Log Handler
# ─────────────────────────────────────────────────────────────

class GUILogHandler(logging.Handler):
    """Pipes Python log records into a CTkTextbox."""

    def __init__(self, textbox: ctk.CTkTextbox):
        super().__init__()
        self._box = textbox
        self.setFormatter(
            logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s",
                              datefmt="%H:%M:%S")
        )

    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname

            # Color tag mapping
            color_map = {
                "DEBUG":   C_MUTED,
                "INFO":    C_TEXT,
                "WARNING": C_YELLOW,
                "ERROR":   C_RED,
                "CRITICAL":C_RED,
            }
            color = color_map.get(level, C_TEXT)

            def _insert():
                self._box.configure(state="normal")
                self._box.insert("end", msg + "\n")
                # Scroll to bottom
                self._box.see("end")
                # Prune if > 800 lines
                try:
                    lines = int(self._box.index("end-1c").split(".")[0])
                    if lines > 800:
                        self._box.delete("1.0", f"{lines - 600}.0")
                except Exception:
                    pass
                self._box.configure(state="disabled")

            self._box.after(0, _insert)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# Helper widgets
# ─────────────────────────────────────────────────────────────

def _card(parent, **kw) -> ctk.CTkFrame:
    defaults = dict(fg_color=C_CARD, corner_radius=10,
                    border_width=1, border_color=C_BORDER)
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def _label(parent, text="", size=13, bold=False, color=C_TEXT, **kw):
    weight = "bold" if bold else "normal"
    return ctk.CTkLabel(parent, text=text,
                        font=("Segoe UI", size, weight),
                        text_color=color, **kw)


def _btn(parent, text, command, color=C_BLUE, hover=None, width=160, **kw):
    if hover is None:
        # Slightly lighter shade
        hover = color
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color=color, hover_color=hover,
        corner_radius=8, font=("Segoe UI", 13, "bold"),
        width=width, **kw
    )


def _entry(parent, placeholder="", show=None, width=260, **kw):
    e = ctk.CTkEntry(
        parent, placeholder_text=placeholder,
        fg_color=C_DARK, border_color=C_BORDER,
        text_color=C_TEXT, placeholder_text_color=C_MUTED,
        font=FONT_MONO, corner_radius=7,
        width=width, show=show, **kw
    )
    return e


# ─────────────────────────────────────────────────────────────
# Main Application Window
# ─────────────────────────────────────────────────────────────

class MorningStarApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # State
        self._app_instance  = None          # trading App()
        self._app_thread    = None
        self._is_running    = False
        self._ws_log_handler: Optional[GUILogHandler] = None
        self._blink_state   = True

        # ── Window ────────────────────────────────────────────
        self.title("Balfund — Morning Star / Evening Star Strategy")
        self.geometry("1280x760")
        self.minsize(1100, 680)
        self.configure(fg_color=C_BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Layout scaffolding ────────────────────────────────
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_body()
        self._build_statusbar()

        # ── Load .env on start ────────────────────────────────
        self._load_env_to_fields()

        # ── Start update loop ─────────────────────────────────
        self.after(600, self._update_loop)

    # ══════════════════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════════════════

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=C_DARK, corner_radius=0, height=62)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(2, weight=1)

        # Logo / Brand
        _label(hdr, "⭐", size=22, color=C_YELLOW).grid(
            row=0, column=0, padx=(18, 4), pady=14)
        _label(hdr, "Morning Star / Evening Star", size=17, bold=True,
               color=C_TEXT).grid(row=0, column=1, padx=(0, 6))
        _label(hdr, "NIFTY Weekly Options  ·  Dhan API v2",
               size=11, color=C_MUTED).grid(row=0, column=2,
                                             padx=4, sticky="w")

        # Right: mode badge + clock
        right = ctk.CTkFrame(hdr, fg_color="transparent")
        right.grid(row=0, column=3, padx=18, sticky="e")

        self._mode_lbl = _label(right, "◉  PAPER MODE", size=12, bold=True,
                                color=C_YELLOW)
        self._mode_lbl.pack(side="left", padx=(0, 20))

        self._clock_lbl = _label(right, "", size=13, color=C_MUTED)
        self._clock_lbl.pack(side="left")

    # ══════════════════════════════════════════════════════════
    # BODY  (tabview)
    # ══════════════════════════════════════════════════════════

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self._tabs = ctk.CTkTabview(
            body,
            fg_color=C_PANEL,
            segmented_button_fg_color=C_DARK,
            segmented_button_selected_color=C_BLUE,
            segmented_button_selected_hover_color="#3a8eee",
            segmented_button_unselected_color=C_DARK,
            segmented_button_unselected_hover_color=C_BORDER,
            text_color=C_TEXT,
            corner_radius=12,
            border_width=1,
            border_color=C_BORDER,
        )
        self._tabs.grid(row=0, column=0, sticky="nsew", padx=12, pady=(8, 4))

        for tab_name in ["📊  Dashboard", "🔑  Token Manager",
                          "⚙️  Settings", "📋  Trade Log"]:
            self._tabs.add(tab_name)

        self._build_dashboard(self._tabs.tab("📊  Dashboard"))
        self._build_token_tab(self._tabs.tab("🔑  Token Manager"))
        self._build_settings_tab(self._tabs.tab("⚙️  Settings"))
        self._build_log_tab(self._tabs.tab("📋  Trade Log"))

    # ══════════════════════════════════════════════════════════
    # DASHBOARD TAB
    # ══════════════════════════════════════════════════════════

    def _build_dashboard(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # ── Top row: 3 stat cards ──────────────────────────────
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=2, sticky="ew",
                 padx=10, pady=(10, 6))
        top.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Card 1 — NIFTY LTP
        c1 = _card(top)
        c1.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        _label(c1, "NIFTY 50  INDEX", size=11, color=C_MUTED
               ).pack(anchor="w", padx=14, pady=(12, 0))
        self._ltp_lbl = _label(c1, "——", size=30, bold=True, color=C_TEXT)
        self._ltp_lbl.pack(anchor="w", padx=14)
        self._ltp_chg_lbl = _label(c1, "", size=12, color=C_MUTED)
        self._ltp_chg_lbl.pack(anchor="w", padx=14, pady=(0, 12))

        # Card 2 — Session
        c2 = _card(top)
        c2.grid(row=0, column=1, sticky="ew", padx=3)
        _label(c2, "SESSION STATUS", size=11, color=C_MUTED
               ).pack(anchor="w", padx=14, pady=(12, 0))
        self._session_lbl = _label(c2, "PRE-SESSION", size=18,
                                    bold=True, color=C_MUTED)
        self._session_lbl.pack(anchor="w", padx=14, pady=(2, 0))
        self._session_time_lbl = _label(c2, "", size=12, color=C_MUTED)
        self._session_time_lbl.pack(anchor="w", padx=14, pady=(0, 12))

        # Card 3 — Trades
        c3 = _card(top)
        c3.grid(row=0, column=2, sticky="ew", padx=3)
        _label(c3, "TRADES TODAY", size=11, color=C_MUTED
               ).pack(anchor="w", padx=14, pady=(12, 0))
        self._trade_count_lbl = _label(c3, "0 / 5", size=18,
                                        bold=True, color=C_TEXT)
        self._trade_count_lbl.pack(anchor="w", padx=14, pady=(2, 0))
        self._day_pnl_lbl = _label(c3, "Day P&L: ——", size=12, color=C_MUTED)
        self._day_pnl_lbl.pack(anchor="w", padx=14, pady=(0, 12))

        # Card 4 — WS status
        c4 = _card(top)
        c4.grid(row=0, column=3, sticky="ew", padx=(6, 0))
        _label(c4, "CONNECTION", size=11, color=C_MUTED
               ).pack(anchor="w", padx=14, pady=(12, 0))
        self._ws_lbl = _label(c4, "⬤  Offline", size=14,
                               bold=True, color=C_RED)
        self._ws_lbl.pack(anchor="w", padx=14, pady=(4, 0))
        self._ws_sub_lbl = _label(c4, "Strategy not running", size=11,
                                   color=C_MUTED)
        self._ws_sub_lbl.pack(anchor="w", padx=14, pady=(0, 12))

        # ── Bottom row: left panel + right log ────────────────
        left = ctk.CTkFrame(parent, fg_color="transparent", width=360)
        left.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 8))
        left.grid_propagate(False)
        left.grid_rowconfigure(3, weight=1)

        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 8))
        right.grid_rowconfigure(1, weight=1)

        # ── Left: Active Trade ─────────────────────────────────
        trade_card = _card(left)
        trade_card.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        trade_card.grid_columnconfigure(1, weight=1)

        hrow = ctk.CTkFrame(trade_card, fg_color="transparent")
        hrow.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 0))
        _label(hrow, "ACTIVE TRADE", size=11, color=C_MUTED, bold=True
               ).pack(side="left")
        self._trade_status_badge = _label(hrow, "  NO TRADE  ", size=10,
                                           color=C_MUTED)
        self._trade_status_badge.pack(side="right")

        self._trade_name_lbl = _label(trade_card, "——", size=14,
                                       bold=True, color=C_TEXT)
        self._trade_name_lbl.grid(row=1, column=0, columnspan=2,
                                   sticky="w", padx=12, pady=(4, 0))

        self._trade_entry_lbl = _label(trade_card, "Entry: ——", size=12, color=C_MUTED)
        self._trade_entry_lbl.grid(row=2, column=0, sticky="w", padx=12)
        self._trade_sl_lbl = _label(trade_card, "SL: ——", size=12, color=C_RED)
        self._trade_sl_lbl.grid(row=3, column=0, sticky="w", padx=12)
        self._trade_tp_lbl = _label(trade_card, "TP: ——", size=12, color=C_GREEN)
        self._trade_tp_lbl.grid(row=4, column=0, sticky="w", padx=12)
        self._trade_pnl_lbl = _label(trade_card, "P&L: ——", size=16,
                                      bold=True, color=C_TEXT)
        self._trade_pnl_lbl.grid(row=2, column=1, rowspan=3,
                                  sticky="e", padx=14, pady=(0, 4))
        ctk.CTkFrame(trade_card, height=1, fg_color=C_BORDER
                     ).grid(row=5, column=0, columnspan=2,
                            sticky="ew", padx=12, pady=(6, 0))
        self._trade_qty_lbl = _label(trade_card, "Qty: ——  |  Expiry: ——",
                                      size=11, color=C_MUTED)
        self._trade_qty_lbl.grid(row=6, column=0, columnspan=2,
                                  sticky="w", padx=12, pady=(4, 10))

        # ── Left: Pending Signal ───────────────────────────────
        sig_card = _card(left)
        sig_card.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        _label(sig_card, "PENDING SIGNAL", size=11, color=C_MUTED, bold=True
               ).pack(anchor="w", padx=12, pady=(10, 2))
        self._sig_pattern_lbl = _label(sig_card, "No signal", size=13,
                                        bold=True, color=C_MUTED)
        self._sig_pattern_lbl.pack(anchor="w", padx=12)
        self._sig_trigger_lbl = _label(sig_card, "", size=12, color=C_MUTED)
        self._sig_trigger_lbl.pack(anchor="w", padx=12)
        self._sig_window_lbl  = _label(sig_card, "", size=11, color=C_MUTED)
        self._sig_window_lbl.pack(anchor="w", padx=12, pady=(0, 10))

        # ── Left: Last Candle ──────────────────────────────────
        candle_card = _card(left)
        candle_card.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        candle_card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        _label(candle_card, "LAST CLOSED CANDLE (1m)", size=11,
               color=C_MUTED, bold=True
               ).grid(row=0, column=0, columnspan=4,
                      sticky="w", padx=12, pady=(10, 4))

        self._c_time_lbl = _label(candle_card, "——", size=11, color=C_MUTED)
        self._c_time_lbl.grid(row=0, column=3, sticky="e", padx=12)

        for col, key, lbl_attr, col_color in [
            (0, "O", "_c_open_lbl",  C_TEXT),
            (1, "H", "_c_high_lbl",  C_GREEN),
            (2, "L", "_c_low_lbl",   C_RED),
            (3, "C", "_c_close_lbl", C_BLUE),
        ]:
            f = ctk.CTkFrame(candle_card, fg_color=C_DARK, corner_radius=6)
            f.grid(row=1, column=col, padx=(12 if col == 0 else 4,
                                            12 if col == 3 else 4),
                   pady=(0, 10), sticky="ew")
            _label(f, key, size=10, color=C_MUTED).pack(pady=(6, 0))
            lbl = _label(f, "——", size=14, bold=True, color=col_color)
            lbl.pack(pady=(0, 6), padx=8)
            setattr(self, lbl_attr, lbl)

        # ── Left: Start / Stop controls ───────────────────────
        ctrl = _card(left)
        ctrl.grid(row=3, column=0, sticky="sew", pady=(0, 0))
        ctrl.grid_columnconfigure((0, 1), weight=1)

        self._start_btn = _btn(ctrl, "▶  Start Strategy",
                                self._start_strategy,
                                color=C_GREEN, hover_color="#0ea570")
        self._start_btn.grid(row=0, column=0, padx=(12, 4), pady=14, sticky="ew")

        self._stop_btn = _btn(ctrl, "■  Stop",
                               self._stop_strategy,
                               color=C_RED, hover_color="#dc3545",
                               state="disabled")
        self._stop_btn.grid(row=0, column=1, padx=(4, 12), pady=14, sticky="ew")

        # Paper/Live toggle
        switch_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        switch_row.grid(row=1, column=0, columnspan=2,
                        padx=12, pady=(0, 12), sticky="w")
        _label(switch_row, "Paper Mode", size=12, color=C_MUTED).pack(side="left")
        self._paper_switch = ctk.CTkSwitch(
            switch_row, text="", width=46,
            fg_color=C_BORDER, progress_color=C_YELLOW,
            command=self._on_paper_toggle,
        )
        self._paper_switch.pack(side="left", padx=8)
        self._paper_switch.select()       # default ON

        # ── Right: Live Console ────────────────────────────────
        _label(right, "LIVE CONSOLE", size=11, color=C_MUTED, bold=True
               ).grid(row=0, column=0, sticky="w", padx=4, pady=(0, 4))

        self._console = ctk.CTkTextbox(
            right,
            font=FONT_MONO,
            fg_color=C_DARK,
            text_color="#8fb8d8",
            corner_radius=8,
            border_width=1,
            border_color=C_BORDER,
            state="disabled",
            wrap="word",
        )
        self._console.grid(row=1, column=0, sticky="nsew")

        # Attach GUI log handler
        self._gui_log = GUILogHandler(self._console)
        self._gui_log.setLevel(logging.INFO)
        logging.getLogger().addHandler(self._gui_log)

    # ══════════════════════════════════════════════════════════
    # TOKEN MANAGER TAB
    # ══════════════════════════════════════════════════════════

    def _build_token_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        # ── Credentials card ─────────────────────────────────
        cred_card = _card(parent)
        cred_card.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))

        _label(cred_card, "  🔐  DHAN API CREDENTIALS", size=13, bold=True,
               color=C_BLUE).grid(row=0, column=0, columnspan=4,
                                   sticky="w", padx=14, pady=(14, 8))

        # Row labels + entries
        fields = [
            ("Client ID",     "DHAN_CLIENT_ID",    "_cred_client_id",  None,  320),
            ("Trading PIN",   "DHAN_PIN",           "_cred_pin",        "●",  160),
            ("TOTP Secret",   "DHAN_TOTP_SECRET",   "_cred_totp",       None,  400),
        ]
        for i, (label, env_key, attr, show, width) in enumerate(fields):
            _label(cred_card, label, size=12, color=C_MUTED
                   ).grid(row=i+1, column=0, sticky="w", padx=(16, 6), pady=6)
            e = _entry(cred_card, placeholder=f"Enter {label}",
                       show=show, width=width)
            e.grid(row=i+1, column=1, sticky="w", padx=(0, 14), pady=6)
            setattr(self, attr, e)

        # ── Current Token card ────────────────────────────────
        tok_card = _card(parent)
        tok_card.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
        tok_card.grid_columnconfigure(1, weight=1)

        _label(tok_card, "  📋  ACCESS TOKEN", size=13, bold=True,
               color=C_BLUE).grid(row=0, column=0, columnspan=3,
                                   sticky="w", padx=14, pady=(14, 6))

        self._token_display = _entry(tok_card, placeholder="No token yet",
                                      width=560)
        self._token_display.grid(row=1, column=0, columnspan=2,
                                  sticky="ew", padx=14, pady=(0, 4))

        self._token_expiry_lbl = _label(tok_card, "Expiry: ——",
                                         size=11, color=C_MUTED)
        self._token_expiry_lbl.grid(row=2, column=0, sticky="w",
                                     padx=14, pady=(0, 2))

        self._token_status_lbl = _label(tok_card, "⬤  Not verified",
                                         size=12, color=C_MUTED)
        self._token_status_lbl.grid(row=2, column=1, sticky="e",
                                     padx=14, pady=(0, 2))

        # ── Action buttons ────────────────────────────────────
        btn_row = ctk.CTkFrame(tok_card, fg_color="transparent")
        btn_row.grid(row=3, column=0, columnspan=3,
                     padx=10, pady=(6, 14), sticky="w")

        _btn(btn_row, "⚡  Generate Token",
             self._generate_token, color=C_GREEN,
             hover_color="#0ea570", width=180
             ).pack(side="left", padx=(4, 6))

        _btn(btn_row, "✅  Verify Token",
             self._verify_token, color=C_BLUE,
             hover_color="#3a8eee", width=160
             ).pack(side="left", padx=(0, 6))

        _btn(btn_row, "💾  Save to .env",
             self._save_credentials, color=C_PURPLE,
             hover_color="#9333ea", width=160
             ).pack(side="left", padx=(0, 6))

        _btn(btn_row, "🔄  Renew Token",
             self._renew_token, color="#f59e0b",
             hover_color="#d97706", width=160
             ).pack(side="left", padx=(0, 4))

        # ── Auto-refresh section ──────────────────────────────
        auto_card = _card(parent)
        auto_card.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 8))

        _label(auto_card, "  ⏰  AUTO-REFRESH", size=13, bold=True,
               color=C_BLUE).grid(row=0, column=0, columnspan=3,
                                   sticky="w", padx=14, pady=(14, 6))

        row_frame = ctk.CTkFrame(auto_card, fg_color="transparent")
        row_frame.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 14))

        self._auto_refresh_switch = ctk.CTkSwitch(
            row_frame, text="Enable daily auto-refresh",
            font=("Segoe UI", 13),
            fg_color=C_BORDER, progress_color=C_GREEN,
            text_color=C_TEXT,
        )
        self._auto_refresh_switch.pack(side="left", padx=(0, 20))

        _label(row_frame, "Refresh at:", size=12, color=C_MUTED
               ).pack(side="left", padx=(0, 6))
        self._refresh_time_entry = _entry(row_frame, placeholder="08:00", width=90)
        self._refresh_time_entry.pack(side="left", padx=(0, 12))
        self._refresh_time_entry.insert(0, "08:00")

        _btn(row_frame, "▶  Start Daemon",
             self._start_token_daemon, color=C_YELLOW,
             hover_color="#d97706", width=150, text_color=C_DARK
             ).pack(side="left")

        # ── Token log ─────────────────────────────────────────
        self._token_log = ctk.CTkTextbox(
            parent, font=FONT_MONO,
            fg_color=C_DARK, text_color="#8fb8d8",
            corner_radius=8, border_width=1, border_color=C_BORDER,
            state="disabled", height=160,
        )
        self._token_log.grid(row=3, column=0, sticky="ew",
                              padx=20, pady=(0, 12))

    def _log_token(self, msg: str, color_tag: str = "info"):
        def _insert():
            self._token_log.configure(state="normal")
            ts = datetime.now().strftime("%H:%M:%S")
            self._token_log.insert("end", f"[{ts}]  {msg}\n")
            self._token_log.see("end")
            self._token_log.configure(state="disabled")
        self._token_log.after(0, _insert)

    def _generate_token(self):
        """Generate fresh token via TOTP."""
        self._log_token("⚡ Generating token via TOTP...")
        cid   = self._cred_client_id.get().strip()
        pin   = self._cred_pin.get().strip()
        totp  = self._cred_totp.get().strip()

        if not (cid and pin and totp):
            self._log_token("❌ Please fill Client ID, PIN and TOTP Secret first.")
            return

        def _work():
            try:
                from dhan_token_manager import generate_token_via_totp
                result = generate_token_via_totp(cid, pin, totp)
                if result["success"]:
                    token = result["access_token"]
                    expiry = result.get("expiry", "")
                    name   = result.get("client_name", "")
                    self._token_display.delete(0, "end")
                    self._token_display.insert(0, token)
                    self.after(0, lambda: self._token_expiry_lbl.configure(
                        text=f"Expiry: {expiry}  |  Client: {name}"))
                    self.after(0, lambda: self._token_status_lbl.configure(
                        text="⬤  Token Generated", text_color=C_GREEN))
                    self._log_token(f"✅ Token generated! Client: {name}  Expires: {expiry}")
                    # Auto-save to .env
                    self.after(0, self._save_credentials)
                else:
                    err = result.get("error", "Unknown error")
                    self._log_token(f"❌ Generation failed: {err}")
                    self.after(0, lambda: self._token_status_lbl.configure(
                        text="⬤  Generation Failed", text_color=C_RED))
            except Exception as e:
                self._log_token(f"❌ Exception: {e}")

        threading.Thread(target=_work, daemon=True).start()

    def _verify_token(self):
        """Verify the current token."""
        token = self._token_display.get().strip()
        cid   = self._cred_client_id.get().strip()
        if not (token and cid):
            self._log_token("❌ Enter Client ID and Token first.")
            return
        self._log_token("🔍 Verifying token...")

        def _work():
            try:
                from dhan_token_manager import verify_token
                ok = verify_token(cid, token)
                if ok:
                    self._log_token("✅ Token is valid!")
                    self.after(0, lambda: self._token_status_lbl.configure(
                        text="⬤  Valid", text_color=C_GREEN))
                else:
                    self._log_token("⚠️  Token is invalid or expired.")
                    self.after(0, lambda: self._token_status_lbl.configure(
                        text="⬤  Invalid / Expired", text_color=C_RED))
            except Exception as e:
                self._log_token(f"❌ Verify error: {e}")

        threading.Thread(target=_work, daemon=True).start()

    def _renew_token(self):
        """Renew existing token."""
        token = self._token_display.get().strip()
        cid   = self._cred_client_id.get().strip()
        if not (token and cid):
            self._log_token("❌ Need Client ID and existing token to renew.")
            return
        self._log_token("🔄 Renewing token...")

        def _work():
            try:
                from dhan_token_manager import renew_token
                result = renew_token(cid, token)
                if result["success"]:
                    new_tok = result["access_token"]
                    expiry  = result.get("expiry", "")
                    self._token_display.delete(0, "end")
                    self._token_display.insert(0, new_tok)
                    self.after(0, lambda: self._token_expiry_lbl.configure(
                        text=f"Expiry: {expiry}"))
                    self.after(0, lambda: self._token_status_lbl.configure(
                        text="⬤  Renewed", text_color=C_GREEN))
                    self._log_token(f"✅ Token renewed! Expires: {expiry}")
                    self.after(0, self._save_credentials)
                else:
                    self._log_token(f"⚠️  Renew failed: {result.get('error')}")
            except Exception as e:
                self._log_token(f"❌ Renew error: {e}")

        threading.Thread(target=_work, daemon=True).start()

    def _save_credentials(self):
        """Save fields to .env file."""
        cid   = self._cred_client_id.get().strip()
        pin   = self._cred_pin.get().strip()
        totp  = self._cred_totp.get().strip()
        token = self._token_display.get().strip()

        try:
            if not ENV_FILE.exists():
                ENV_FILE.write_text("")
            if cid:
                set_key(str(ENV_FILE), "DHAN_CLIENT_ID", cid)
            if pin:
                set_key(str(ENV_FILE), "DHAN_PIN", pin)
            if totp:
                set_key(str(ENV_FILE), "DHAN_TOTP_SECRET", totp)
            if token:
                set_key(str(ENV_FILE), "DHAN_ACCESS_TOKEN", token)
            self._log_token("💾 Credentials saved to .env")
        except Exception as e:
            self._log_token(f"❌ Save failed: {e}")

    def _start_token_daemon(self):
        """Start background token refresh daemon."""
        if not self._auto_refresh_switch.get():
            self._log_token("⚠️  Enable auto-refresh switch first.")
            return
        refresh_time = self._refresh_time_entry.get().strip() or "08:00"
        self._log_token(f"🚀 Token daemon started. Will refresh daily at {refresh_time}")

        def _daemon():
            try:
                from dhan_token_manager import run_daemon
                run_daemon(refresh_time=refresh_time)
            except Exception as e:
                self._log_token(f"❌ Daemon error: {e}")

        threading.Thread(target=_daemon, daemon=True).start()

    # ══════════════════════════════════════════════════════════
    # SETTINGS TAB
    # ══════════════════════════════════════════════════════════

    def _build_settings_tab(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)

        _label(parent, "  ⚙️  Strategy Configuration", size=14, bold=True,
               color=C_TEXT).grid(row=0, column=0, columnspan=2,
                                   sticky="w", padx=14, pady=(14, 6))
        _label(parent, "Changes take effect on next Strategy Start",
               size=11, color=C_MUTED
               ).grid(row=1, column=0, columnspan=2, sticky="w", padx=14,
                      pady=(0, 10))

        # Config params to expose
        self._cfg_fields = {}
        cfg_params = [
            # (label, env_key_or_attr, default, col, row)
            ("Paper Trade Mode",      "PAPER_TRADE",         "True",  0, 0),
            ("Target Delta",          "TARGET_DELTA",        "0.60",  0, 1),
            ("Session Start (HH:MM)", "SESSION_START_TIME",  "09:29", 0, 2),
            ("Last Entry (HH:MM)",    "LAST_ENTRY_TIME",     "14:45", 0, 3),
            ("Cancel Pending (HH:MM)","CANCEL_PENDING_TIME", "15:10", 0, 4),
            ("Force Exit (HH:MM)",    "FORCE_EXIT_TIME",     "15:15", 0, 5),
            ("Large Body Ratio",      "LARGE_BODY_RATIO",    "0.60",  1, 0),
            ("Small Body Ratio",      "SMALL_BODY_RATIO",    "0.35",  1, 1),
            ("Min Candle Range (pts)","MIN_CANDLE_RANGE",    "0.5",   1, 2),
            ("Entry Buffer (pts)",    "ENTRY_BUFFER_OPTIONS","1.0",   1, 3),
            ("Entry Window (candles)","ENTRY_CANDLE_WINDOW", "2",     1, 4),
            ("Risk/Reward Ratio",     "RISK_REWARD_RATIO",   "1.5",   1, 5),
            ("Max Trades/Day",        "MAX_TRADES_PER_DAY",  "5",     0, 6),
            ("Lot Size",              "LOT_SIZE",            "75",    1, 6),
        ]

        col_frames = [_card(parent), _card(parent)]
        col_frames[0].grid(row=2, column=0, sticky="nsew", padx=(14, 6), pady=4)
        col_frames[1].grid(row=2, column=1, sticky="nsew", padx=(6, 14), pady=4)

        for label, key, default, col, row in cfg_params:
            f = col_frames[col]
            _label(f, label, size=12, color=C_MUTED
                   ).grid(row=row*2, column=0, sticky="w",
                          padx=14, pady=(10, 0))
            e = _entry(f, placeholder=default, width=180)
            e.grid(row=row*2+1, column=0, sticky="w", padx=14, pady=(2, 0))
            self._cfg_fields[key] = e

        # Load current config values
        self._load_config_to_settings()

        # Save button
        _btn(parent, "💾  Save Settings to .env",
             self._save_settings, color=C_PURPLE,
             hover_color="#9333ea", width=220
             ).grid(row=3, column=0, columnspan=2,
                    padx=14, pady=14, sticky="w")

    def _load_config_to_settings(self):
        """Pre-fill settings from config.py values."""
        try:
            import config as cfg
            mapping = {
                "PAPER_TRADE":         str(cfg.PAPER_TRADE),
                "TARGET_DELTA":        str(cfg.TARGET_DELTA),
                "SESSION_START_TIME":  cfg.SESSION_START_TIME,
                "LAST_ENTRY_TIME":     cfg.LAST_ENTRY_TIME,
                "CANCEL_PENDING_TIME": cfg.CANCEL_PENDING_TIME,
                "FORCE_EXIT_TIME":     cfg.FORCE_EXIT_TIME,
                "LARGE_BODY_RATIO":    str(cfg.LARGE_BODY_RATIO),
                "SMALL_BODY_RATIO":    str(cfg.SMALL_BODY_RATIO),
                "MIN_CANDLE_RANGE":    str(cfg.MIN_CANDLE_RANGE),
                "ENTRY_BUFFER_OPTIONS":str(cfg.ENTRY_BUFFER_OPTIONS),
                "ENTRY_CANDLE_WINDOW": str(cfg.ENTRY_CANDLE_WINDOW),
                "RISK_REWARD_RATIO":   str(cfg.RISK_REWARD_RATIO),
                "MAX_TRADES_PER_DAY":  str(cfg.MAX_TRADES_PER_DAY),
                "LOT_SIZE":            str(cfg.LOT_SIZE),
            }
            for key, val in mapping.items():
                if key in self._cfg_fields:
                    self._cfg_fields[key].delete(0, "end")
                    self._cfg_fields[key].insert(0, val)
        except Exception:
            pass

    def _save_settings(self):
        """Save settings as env vars to .env."""
        if not ENV_FILE.exists():
            ENV_FILE.write_text("")
        saved = []
        for key, entry in self._cfg_fields.items():
            val = entry.get().strip()
            if val:
                set_key(str(ENV_FILE), key, val)
                saved.append(key)
        logging.getLogger("settings").info(
            f"Settings saved to .env: {', '.join(saved)}"
        )

    # ══════════════════════════════════════════════════════════
    # TRADE LOG TAB
    # ══════════════════════════════════════════════════════════

    def _build_log_tab(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Summary row
        summ = ctk.CTkFrame(parent, fg_color="transparent")
        summ.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 6))

        self._log_summary_lbl = _label(summ, "No trades this session.",
                                        size=13, color=C_MUTED)
        self._log_summary_lbl.pack(side="left")

        _btn(summ, "🗑  Clear Log", self._clear_log,
             color=C_BORDER, hover_color=C_MUTED,
             width=120, text_color=C_TEXT
             ).pack(side="right", padx=4)

        # Header row
        hdr_frame = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=8,
                                  height=36)
        hdr_frame.grid(row=0, column=0, sticky="ew", padx=14, pady=(40, 0))
        hdr_frame.grid_propagate(False)
        hdr_cols = ["#", "Time", "Direction", "Option", "Entry", "Exit",
                    "Reason", "P&L"]
        hdr_widths = [30, 80, 80, 200, 80, 80, 90, 90]
        for ci, (hdr, w) in enumerate(zip(hdr_cols, hdr_widths)):
            _label(hdr_frame, hdr, size=11, bold=True, color=C_MUTED
                   ).place(x=sum(hdr_widths[:ci]) + 10, rely=0.5, anchor="w")

        # Scrollable trade rows
        self._log_scroll = ctk.CTkScrollableFrame(
            parent, fg_color=C_DARK,
            corner_radius=8, border_width=1, border_color=C_BORDER,
        )
        self._log_scroll.grid(row=1, column=0, sticky="nsew",
                               padx=14, pady=(0, 12))

        self._log_row_frames = []

    def _refresh_trade_log(self):
        """Redraw the trade log from tracker data."""
        if not self._app_instance:
            return
        log = self._app_instance.strategy.tracker.get_trade_log()

        # Clear existing
        for w in self._log_scroll.winfo_children():
            w.destroy()

        if not log:
            _label(self._log_scroll, "No trades recorded this session.",
                   size=12, color=C_MUTED).pack(pady=20)
            return

        total_pnl = sum(t.get("pnl", 0) or 0 for t in log)
        self._log_summary_lbl.configure(
            text=f"{len(log)} trade(s)  |  Day P&L: "
                 f"{'▲' if total_pnl >= 0 else '▼'} ₹{total_pnl:+,.2f}"
        )

        hdr = ctk.CTkFrame(self._log_scroll,
                            fg_color=C_BORDER, corner_radius=6)
        hdr.pack(fill="x", padx=4, pady=(4, 2))
        for ci, (h, w) in enumerate(zip(
            ["#", "Time", "Dir", "Option", "Entry", "Exit", "Reason", "P&L"],
            [30, 80, 50, 220, 80, 80, 80, 100]
        )):
            _label(hdr, h, size=11, bold=True, color=C_MUTED
                   ).pack(side="left", padx=6)

        for t in reversed(log):
            pnl_val = t.get("pnl")
            pnl_str = f"₹{pnl_val:+,.2f}" if pnl_val is not None else "OPEN"
            pnl_col = C_GREEN if (pnl_val or 0) >= 0 else C_RED
            direction = t.get("type", "?")
            dir_col = C_GREEN if direction == "BUY" else C_RED

            row = ctk.CTkFrame(self._log_scroll, fg_color=C_CARD,
                                corner_radius=6, height=36)
            row.pack(fill="x", padx=4, pady=2)

            fields = [
                (str(t.get("trade_no", "")),  C_MUTED, 30),
                (t.get("entry_time", ""),      C_MUTED, 80),
                (direction,                    dir_col, 50),
                (t.get("option", "?"),         C_TEXT,  220),
                (f"{t.get('entry', 0):.2f}",   C_TEXT,  80),
                (f"{t.get('exit', 0):.2f}" if t.get("exit") else "——",
                                               C_MUTED, 80),
                (t.get("exit_reason", "——"),   C_MUTED, 80),
                (pnl_str,                      pnl_col, 100),
            ]
            for text, color, w in fields:
                _label(row, text, size=12, color=color).pack(
                    side="left", padx=6, pady=6)

    def _clear_log(self):
        for w in self._log_scroll.winfo_children():
            w.destroy()
        self._log_summary_lbl.configure(text="Log cleared.")

    # ══════════════════════════════════════════════════════════
    # STATUS BAR
    # ══════════════════════════════════════════════════════════

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color=C_DARK, height=28, corner_radius=0)
        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_columnconfigure(2, weight=1)

        self._sb_status = _label(bar, "  Ready", size=11, color=C_MUTED)
        self._sb_status.grid(row=0, column=0, padx=8)

        ctk.CTkFrame(bar, width=1, height=14, fg_color=C_BORDER
                     ).grid(row=0, column=1, padx=4)

        self._sb_version = _label(bar, "v1.0.0  ·  Balfund Trading Pvt. Ltd.",
                                   size=10, color=C_MUTED)
        self._sb_version.grid(row=0, column=3, padx=12, sticky="e")

    # ══════════════════════════════════════════════════════════
    # STRATEGY CONTROL
    # ══════════════════════════════════════════════════════════

    def _start_strategy(self):
        if self._is_running:
            return

        # Reload env + config
        load_dotenv(override=True)
        try:
            import config
            importlib.reload(config)
        except Exception as e:
            self._set_status(f"Config error: {e}", C_RED)
            return

        import config as cfg
        if not cfg.DHAN_CLIENT_ID or not cfg.DHAN_ACCESS_TOKEN:
            self._set_status(
                "❌ DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN missing. "
                "Generate token first.", C_RED
            )
            logging.getLogger("gui").error(
                "Cannot start: credentials missing in .env"
            )
            return

        self._is_running = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._set_status("▶ Strategy running...", C_GREEN)

        paper = bool(self._paper_switch.get())
        self._mode_lbl.configure(
            text="◉  PAPER MODE" if paper else "◉  LIVE MODE",
            text_color=C_YELLOW if paper else C_RED
        )

        def _run():
            try:
                # Re-import fresh App from main.py
                import main as m
                importlib.reload(m)
                self._app_instance = m.App()
                self._app_instance.start()
                # Keep thread alive while running
                while self._is_running:
                    time.sleep(0.5)
            except Exception as e:
                logging.getLogger("gui").error(f"Strategy error: {e}")
                self.after(0, self._on_strategy_crash, str(e))

        self._app_thread = threading.Thread(target=_run, daemon=True)
        self._app_thread.start()

    def _stop_strategy(self):
        if not self._is_running:
            return
        self._is_running = False
        if self._app_instance:
            try:
                self._app_instance.stop()
            except Exception:
                pass
            self._app_instance = None

        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._set_status("■ Strategy stopped.", C_MUTED)
        self._ws_lbl.configure(text="⬤  Offline", text_color=C_RED)
        self._ws_sub_lbl.configure(text="Strategy not running")

    def _on_strategy_crash(self, error: str):
        self._is_running = False
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._set_status(f"⚠ Strategy crashed: {error}", C_RED)

    def _on_paper_toggle(self):
        paper = bool(self._paper_switch.get())
        set_key(str(ENV_FILE) if ENV_FILE.exists() else ".env",
                "PAPER_TRADE", str(paper))

    # ══════════════════════════════════════════════════════════
    # .env LOADER
    # ══════════════════════════════════════════════════════════

    def _load_env_to_fields(self):
        load_dotenv()
        mapping = {
            "_cred_client_id": "DHAN_CLIENT_ID",
            "_cred_pin":        "DHAN_PIN",
            "_cred_totp":       "DHAN_TOTP_SECRET",
        }
        for attr, env_key in mapping.items():
            val = os.getenv(env_key, "").strip()
            if val:
                e = getattr(self, attr, None)
                if e:
                    e.delete(0, "end")
                    e.insert(0, val)

        token = os.getenv("DHAN_ACCESS_TOKEN", "").strip()
        if token:
            self._token_display.delete(0, "end")
            self._token_display.insert(0, token)
            self._token_expiry_lbl.configure(
                text=f"Expiry: {os.getenv('DHAN_TOKEN_EXPIRY', '——')}"
            )

    # ══════════════════════════════════════════════════════════
    # LIVE UPDATE LOOP
    # ══════════════════════════════════════════════════════════

    def _update_loop(self):
        try:
            self._update_clock()
            self._update_dashboard()
            self._refresh_trade_log()
        except Exception:
            pass
        self.after(500, self._update_loop)

    def _update_clock(self):
        now = datetime.now(IST)
        self._clock_lbl.configure(text=now.strftime("%H:%M:%S  IST"))
        self._session_time_lbl.configure(text=now.strftime("%d %b %Y"))

    def _update_dashboard(self):
        if not self._is_running or not self._app_instance:
            return

        app = self._app_instance

        # ── LTP ───────────────────────────────────────────────
        try:
            ltp = app.nifty_engine.get_ltp()
            if ltp:
                self._ltp_lbl.configure(text=f"{ltp:,.2f}")
                # Blink green/white to show live
                self._blink_state = not self._blink_state
                col = C_GREEN if self._blink_state else C_TEXT
                self._ltp_lbl.configure(text_color=col)
        except Exception:
            pass

        # ── WS status ─────────────────────────────────────────
        try:
            ws_ok = (app.ws is not None and
                     getattr(app.ws, "sock", None) is not None)
            if ws_ok:
                self._ws_lbl.configure(text="⬤  Connected", text_color=C_GREEN)
                self._ws_sub_lbl.configure(text="NIFTY 50 subscribed")
            else:
                self._ws_lbl.configure(text="⬤  Connecting…", text_color=C_YELLOW)
        except Exception:
            pass

        # ── Session status ────────────────────────────────────
        try:
            status = app.strategy.session.status_str()
            color_map = {
                "TRADING":     C_GREEN,
                "PRE-SESSION": C_MUTED,
                "NO-NEW-ENTRY":C_YELLOW,
                "CANCELLING":  C_YELLOW,
                "FORCE-EXIT":  C_RED,
            }
            self._session_lbl.configure(
                text=status,
                text_color=color_map.get(status, C_MUTED)
            )
        except Exception:
            pass

        # ── Trade count + Day P&L ─────────────────────────────
        try:
            from config import MAX_TRADES_PER_DAY
            cnt  = app.strategy.tracker.daily_trade_count()
            pnl  = app.strategy.tracker.total_pnl()
            self._trade_count_lbl.configure(
                text=f"{cnt} / {MAX_TRADES_PER_DAY}")
            pnl_col = C_GREEN if pnl >= 0 else C_RED
            self._day_pnl_lbl.configure(
                text=f"Day P&L:  ₹{pnl:+,.2f}",
                text_color=pnl_col
            )
        except Exception:
            pass

        # ── Active trade ──────────────────────────────────────
        try:
            trade = app.strategy.tracker.get_active_trade()
            if trade and trade.is_open():
                ltp = app.nifty_engine.get_ltp() or trade.entry_price
                if trade.direction == "BUY":
                    upnl = (ltp - trade.entry_price) * trade.quantity
                else:
                    upnl = (trade.entry_price - ltp) * trade.quantity
                upnl_col = C_GREEN if upnl >= 0 else C_RED
                arrow = "▲" if upnl >= 0 else "▼"

                self._trade_name_lbl.configure(
                    text=trade.display_name, text_color=C_TEXT)
                self._trade_entry_lbl.configure(
                    text=f"Entry: {trade.entry_price:.2f}")
                self._trade_sl_lbl.configure(
                    text=f"SL: {trade.sl_price:.2f}")
                self._trade_tp_lbl.configure(
                    text=f"TP: {trade.tp_price:.2f}")
                self._trade_pnl_lbl.configure(
                    text=f"{arrow} ₹{upnl:+,.2f}",
                    text_color=upnl_col)
                self._trade_qty_lbl.configure(
                    text=f"Qty: {trade.quantity}  |  Expiry: {trade.expiry}")
                dir_col = C_GREEN if trade.direction == "BUY" else C_RED
                self._trade_status_badge.configure(
                    text=f"  {trade.direction}  ",
                    text_color=dir_col)
            else:
                self._trade_name_lbl.configure(
                    text="No open trade", text_color=C_MUTED)
                self._trade_entry_lbl.configure(text="Entry: ——")
                self._trade_sl_lbl.configure(text="SL: ——")
                self._trade_tp_lbl.configure(text="TP: ——")
                self._trade_pnl_lbl.configure(text="——", text_color=C_MUTED)
                self._trade_qty_lbl.configure(text="")
                self._trade_status_badge.configure(
                    text="  NO TRADE  ", text_color=C_MUTED)
        except Exception:
            pass

        # ── Pending signal ────────────────────────────────────
        try:
            sig = app.strategy.tracker.get_pending_signal()
            if sig:
                pat_icon = "☀️" if "MORNING" in sig.pattern_type else "🌆"
                dir_col = C_GREEN if sig.direction == "BUY" else C_RED
                self._sig_pattern_lbl.configure(
                    text=f"{pat_icon}  {sig.pattern_type}  ›  {sig.direction} {sig.option_type}",
                    text_color=dir_col)
                self._sig_trigger_lbl.configure(
                    text=f"Trigger: {sig.entry_trigger:.2f}",
                    text_color=C_YELLOW)
                self._sig_window_lbl.configure(
                    text=f"Entry window: {sig.candles_remaining} candle(s) left")
            else:
                self._sig_pattern_lbl.configure(
                    text="No pending signal", text_color=C_MUTED)
                self._sig_trigger_lbl.configure(text="")
                self._sig_window_lbl.configure(text="")
        except Exception:
            pass

        # ── Last candle ───────────────────────────────────────
        try:
            candles = app.nifty_engine.get_completed_candles()
            if candles:
                c = candles[-1]
                ts = datetime.fromtimestamp(
                    c["bucket"], tz=IST).strftime("%H:%M")
                self._c_time_lbl.configure(text=ts)
                self._c_open_lbl.configure(text=f"{c['open']:.0f}")
                self._c_high_lbl.configure(text=f"{c['high']:.0f}")
                self._c_low_lbl.configure(text=f"{c['low']:.0f}")
                self._c_close_lbl.configure(text=f"{c['close']:.0f}")
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════

    def _set_status(self, msg: str, color=C_MUTED):
        self._sb_status.configure(text=f"  {msg}", text_color=color)

    def _on_close(self):
        self._stop_strategy()
        self.destroy()


# ─────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────

def main():
    app = MorningStarApp()
    app.mainloop()


if __name__ == "__main__":
    main()
