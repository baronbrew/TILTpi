#!/usr/bin/env python3
"""
Tilt Pi lightweight dashboard.

A native Tkinter readout of live Tilt data pulled from the local Node-RED
flow's ``/macid/all`` HTTP endpoint. Built to run on a Raspberry Pi Zero W
(or any 512 MB Pi) with a monitor attached, replacing the Chromium-rendered
node-red-dashboard ``/ui`` page which is too heavy for those boards.

Styled to mirror the node-red-dashboard dark theme and Tilt card layout so it
looks like the ``:1880/ui`` page it replaces. Designed for a 1080p monitor; on
smaller screens it automatically switches to a compact, space-saving layout.

Standard library only -- no pip installs, no browser. Tkinter ships with
Raspberry Pi OS's python3-tk package.

Usage:
    python3 tiltpi_dashboard.py                      # localhost, fullscreen
    python3 tiltpi_dashboard.py --windowed           # development window
    python3 tiltpi_dashboard.py --url http://tiltpi-office:1880/macid/all
    python3 tiltpi_dashboard.py --interval 5
    python3 tiltpi_dashboard.py --compact            # force compact layout
    python3 tiltpi_dashboard.py --full               # force full layout

Keys:
    F11 / f   toggle fullscreen
    Esc / q   quit
"""

import argparse
import json
import os
import queue
import socket
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

DEFAULT_URL = os.environ.get("TILTPI_URL", "http://localhost:1880/macid/all")
DEFAULT_INTERVAL = float(os.environ.get("TILTPI_INTERVAL", "5"))
SITE_NAME = "Tilt Pi"
DESIGN_HEIGHT = 1080  # below this the layout switches to compact

# --- node-red-dashboard dark theme (from the flow's ui_base themeState) ------
PAGE_BG = "#111111"       # page-backgroundColor
TOOLBAR_BG = "#666666"    # page-titlebar-backgroundColor
CARD_BG = "#333333"       # group-backgroundColor
CARD_TEXT = "#eeeeee"     # widget-textColor
GROUP_TEXT = "#8c8c8c"    # group-textColor
BORDER = "#555555"        # group-borderColor
ACCENT = "#4B7930"        # base-color
FONT = "Tahoma"           # base-font (falls back to a sans-serif on the Pi)
MONO = "Courier New"      # h5 footer font in the Tilt card template

STALE_SECONDS = 60

# Base Tilt color -> CSS-accurate background (matches the node-red card divs).
COLOR_MAP = {
    "RED": "#FF0000",
    "GREEN": "#008000",
    "BLACK": "#000000",
    "PURPLE": "#800080",
    "ORANGE": "#FFA500",
    "BLUE": "#0000FF",
    "YELLOW": "#FFFF00",
    "PINK": "#FF1493",   # rendered as DEEPPINK in the template
}

# Bar fill ranges: value maps linearly to 0%..100% across [min, max].
# A value outside the range pegs the bar to 100% (per spec).
SG_MIN, SG_MAX = 0.98, 1.200
TEMP_MIN, TEMP_MAX = 0.0, 185.0

# Per-layout sizing. Negative font sizes are pixels (device-independent).
STYLES = {
    "full": {
        "big": -60, "h1": -15, "h5": -12, "colorbar": 44,
        "pad": 14, "col_w": 380, "side_by_side": False,
    },
    "compact": {
        "big": -32, "h1": -11, "h5": -10, "colorbar": 22,
        "pad": 9, "col_w": 300, "side_by_side": True,
    },
}


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def to_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def bar_fraction(value, lo, hi):
    """0..1 fill for a bar. None -> empty; a value outside [lo, hi] -> full."""
    if value is None:
        return 0.0
    if value < lo or value > hi:
        return 1.0
    return (value - lo) / (hi - lo)


def ui_url_from(data_url):
    """Derive the node-red dashboard /ui address from the data endpoint URL.

    A phone can't reach "localhost", so when the data URL points at this
    machine we substitute its network hostname (adding .local for mDNS).
    """
    parts = urlsplit(data_url)
    scheme = parts.scheme or "http"
    host = parts.hostname or "localhost"
    port = parts.port or 1880
    if host in ("localhost", "127.0.0.1", "::1"):
        host = socket.gethostname()
    # Bare hostnames need ".local" for mDNS resolution from a phone
    # (but leave IPv4/IPv6 literals and already-qualified names alone).
    if "." not in host and ":" not in host:
        host += ".local"
    return f"{scheme}://{host}:{port}/ui"


# --------------------------------------------------------------------------- #
# Data fetching (runs off the Tk main thread so the UI never blocks)
# --------------------------------------------------------------------------- #
class Fetcher(threading.Thread):
    """Polls the Node-RED endpoint on an interval, posting results to a queue."""

    def __init__(self, url, interval, out_queue):
        super().__init__(daemon=True)
        self.url = url
        self.interval = interval
        self.out = out_queue
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        while not self._stop.is_set():
            try:
                with urlopen(self.url, timeout=8) as resp:
                    raw = resp.read().decode("utf-8", "replace")
                data = json.loads(raw)
                if isinstance(data, dict):  # single-tilt response shape
                    data = [data]
                self.out.put(("ok", data))
            except (URLError, OSError) as exc:
                self.out.put(("error", f"connection: {exc}"))
            except (ValueError, json.JSONDecodeError) as exc:
                self.out.put(("error", f"bad data: {exc}"))
            self._stop.wait(self.interval)


# --------------------------------------------------------------------------- #
# A thin colored progress bar (the template's 10px-high div)
# --------------------------------------------------------------------------- #
class Bar(tk.Canvas):
    def __init__(self, master, height=10):
        super().__init__(master, height=height, bg=CARD_BG,
                         highlightthickness=0, bd=0)
        self._fill = 0.0
        self._color = ACCENT
        self.bind("<Configure>", lambda e: self._redraw())

    def set(self, fraction, color):
        self._fill = clamp(fraction, 0, 1)
        self._color = color
        self._redraw()

    def _redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1:
            return
        if self._fill > 0:
            self.create_rectangle(0, 0, w * self._fill, h,
                                  fill=self._color, outline="")


# --------------------------------------------------------------------------- #
# One Tilt card, mirroring the node-red ui_template layout
# --------------------------------------------------------------------------- #
class TiltCard(tk.Frame):
    def __init__(self, master, style):
        super().__init__(master, bg=CARD_BG, bd=0,
                         highlightthickness=1, highlightbackground=BORDER)
        self.style = style
        self.columnconfigure(0, weight=1)

        self.f_h1 = tkfont.Font(family=FONT, size=style["h1"])
        self.f_h1b = tkfont.Font(family=FONT, size=style["h1"], weight="bold")
        self.f_big = tkfont.Font(family=FONT, size=style["big"], weight="bold")
        self.f_h5 = tkfont.Font(family=MONO, size=style["h5"])

        pad = style["pad"]

        # Header: beer name + "TILT | COLOR ..." + full-width color bar.
        self.beer = tk.Label(self, font=self.f_h1, bg=CARD_BG, fg=CARD_TEXT,
                             anchor="w")
        self.beer.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, 0))
        self.title = tk.Label(self, font=self.f_h1b, bg=CARD_BG, fg=CARD_TEXT,
                              anchor="w")
        self.title.grid(row=1, column=0, sticky="ew", padx=pad, pady=(2, 6))
        self.colorbar = tk.Frame(self, bg=CARD_BG, height=style["colorbar"])
        self.colorbar.grid(row=2, column=0, sticky="ew")

        # Readouts: stacked (full) or side-by-side (compact).
        if style["side_by_side"]:
            body = tk.Frame(self, bg=CARD_BG)
            body.grid(row=3, column=0, sticky="ew", padx=pad, pady=(6, 0))
            body.columnconfigure(0, weight=1, uniform="m")
            body.columnconfigure(1, weight=1, uniform="m")
            fg, self.sg_pre, self.sg, self.sg_bar = self._make_metric(body, 0)
            fg.grid(row=0, column=0, sticky="new", padx=(0, 6))
            ft, self.temp_pre, self.temp, self.temp_bar = self._make_metric(body, 0)
            ft.grid(row=0, column=1, sticky="new", padx=(6, 0))
        else:
            fg, self.sg_pre, self.sg, self.sg_bar = self._make_metric(self, pad)
            fg.grid(row=3, column=0, sticky="ew", pady=(8, 0))
            ft, self.temp_pre, self.temp, self.temp_bar = self._make_metric(self, pad)
            ft.grid(row=4, column=0, sticky="ew", pady=(8, 0))

        # Footer: date + freshness/signal (template's centered h5 lines).
        self.date = tk.Label(self, font=self.f_h5, bg=CARD_BG, fg=CARD_TEXT,
                            anchor="center")
        self.date.grid(row=9, column=0, sticky="ew", padx=pad, pady=(8, 0))
        self.foot = tk.Label(self, font=self.f_h5, bg=CARD_BG, fg=CARD_TEXT,
                            anchor="center")
        self.foot.grid(row=10, column=0, sticky="ew", padx=pad, pady=(0, pad))

    def _make_metric(self, parent, lpad):
        """Build a (frame, pre-label, big-label, bar) metric block."""
        f = tk.Frame(parent, bg=CARD_BG)
        f.columnconfigure(0, weight=1)
        pre = tk.Label(f, font=self.f_h1, bg=CARD_BG, fg=CARD_TEXT, anchor="w")
        pre.grid(row=0, column=0, sticky="ew", padx=lpad)
        big = tk.Label(f, font=self.f_big, bg=CARD_BG, fg=CARD_TEXT, anchor="w")
        big.grid(row=1, column=0, sticky="ew", padx=lpad)
        bar = Bar(f)
        bar.grid(row=2, column=0, sticky="ew", pady=(3, 0))
        return f, pre, big, bar

    def update_data(self, d):
        display_color = d.get("displayColor") or [d.get("Color", "?")]
        base = str(display_color[0]).upper()
        swatch = COLOR_MAP.get(base, "#607d8b")
        octets = " ".join(str(x) for x in display_color[1:])
        compact = self.style["side_by_side"]

        beer = d.get("Beer") or ["Untitled"]
        self.beer.config(text=beer[0] if beer and beer[0] else "Untitled")
        self.title.config(text=f"TILT | {base} {octets}".rstrip())
        self.colorbar.config(bg=swatch)

        # Gravity: ferm is the calibrated display value, uncalferm the raw one.
        units = d.get("fermunits", "") or ""
        uncalferm = d.get("uncalferm", "--")
        self.sg_pre.config(text=(f"pre-cal {uncalferm}" if compact
                                 else f"SG/Concentration: {uncalferm} (pre-calibrated)"))
        self.sg.config(text=f"{d.get('ferm', d.get('SG', '--'))}{units}")
        self.sg_bar.set(bar_fraction(to_float(d.get("SG")), SG_MIN, SG_MAX), swatch)

        # Temperature: displayTemp calibrated, displayuncalTemp raw.
        tunits = d.get("tempunits", "") or ""
        uncaltemp = d.get("displayuncalTemp", "--")
        self.temp_pre.config(text=(f"pre-cal {uncaltemp}{tunits}" if compact
                                   else f"Temperature: {uncaltemp} (pre-calibrated)"))
        self.temp.config(text=f"{d.get('displayTemp', d.get('Temp', '--'))}{tunits}")
        self.temp_bar.set(bar_fraction(to_float(d.get("Temp")), TEMP_MIN, TEMP_MAX), swatch)

        # Footer: formatted date, then freshness + signal.
        self.date.config(text=d.get("formatteddate", ""))
        ts = to_float(d.get("timeStamp"))
        stale = False
        if ts is not None:
            age = time.time() - ts / 1000.0
            if 0 <= age < 3600:
                secs = f"Received {int(age)} seconds ago"
                stale = age > STALE_SECONDS
            else:
                secs = "Received - seconds ago"
        else:
            secs = "Received - seconds ago"
        rssi = d.get("rssi", "?")
        flag = "   ⚠ STALE" if stale else ""
        self.foot.config(text=f"{secs}   {rssi} dBm{flag}",
                       fg="#e0a030" if stale else CARD_TEXT)


# --------------------------------------------------------------------------- #
# Main dashboard window
# --------------------------------------------------------------------------- #
class Dashboard(tk.Tk):
    def __init__(self, url, interval, fullscreen, layout):
        super().__init__()
        self.title(f"{SITE_NAME} Dashboard")
        self.configure(bg=PAGE_BG)
        self.url = url
        self._fullscreen = fullscreen

        if layout is None:  # auto-select from the physical screen height
            layout = "compact" if self.winfo_screenheight() < DESIGN_HEIGHT else "full"
        self.style = STYLES[layout]

        self.cards = {}  # mac -> TiltCard
        self.queue = queue.Queue()

        self.f_title = tkfont.Font(family=FONT, size=-18)
        self.f_status = tkfont.Font(family=MONO, size=-12)

        # Toolbar (node-red page titlebar).
        bar = tk.Frame(self, bg=TOOLBAR_BG, height=48)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)
        tk.Label(bar, text="☰", font=self.f_title, bg=TOOLBAR_BG,
                 fg="#ffffff").pack(side="left", padx=(14, 8))
        tk.Label(bar, text=SITE_NAME, font=self.f_title, bg=TOOLBAR_BG,
                 fg="#ffffff").pack(side="left")
        self.status = tk.Label(bar, text="starting…", font=self.f_status,
                              bg=TOOLBAR_BG, fg="#ffffff")
        self.status.pack(side="right", padx=14)
        # Address of the full node-red dashboard — open on a phone to change
        # settings, start logging, switch units, etc.
        tk.Label(bar, text=f"📱 Settings: {ui_url_from(url)}", font=self.f_status,
                 bg=TOOLBAR_BG, fg="#ffffff").pack(side="right", padx=(14, 4))

        self.grid_frame = tk.Frame(self, bg=PAGE_BG)
        self.grid_frame.pack(fill="both", expand=True, padx=6, pady=6)

        self.empty = tk.Label(
            self.grid_frame,
            text="Waiting for Tilt data…\n\nIs Node-RED running and a Tilt floating nearby?",
            font=self.f_title, bg=PAGE_BG, fg=GROUP_TEXT, justify="center")

        self.attributes("-fullscreen", fullscreen)
        if not fullscreen:
            self.geometry("1280x720" if layout == "full" else "960x600")
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<f>", self.toggle_fullscreen)
        self.bind("<Escape>", lambda e: self.close())
        self.bind("<q>", lambda e: self.close())
        self.bind("<Configure>", self._on_resize)

        self.fetcher = Fetcher(url, interval, self.queue)
        self.fetcher.start()
        self.after(200, self._drain)

    def toggle_fullscreen(self, _event=None):
        self._fullscreen = not self._fullscreen
        self.attributes("-fullscreen", self._fullscreen)

    def close(self, _event=None):
        self.fetcher.stop()
        self.destroy()

    def _drain(self):
        latest, error = None, None
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "ok":
                    latest = payload
                else:
                    error = payload
        except queue.Empty:
            pass

        if latest is not None:
            self._render(latest)
            self.status.config(
                text=f"● live   {len(latest)} tilt(s)   {time.strftime('%H:%M:%S')}",
                fg="#b6e3a0")
        elif error is not None:
            self.status.config(text=f"● offline   {error[:60]}", fg="#e0a030")

        self.after(300, self._drain)

    def _render(self, tilts):
        valid = [t for t in tilts
                 if isinstance(t, dict) and (t.get("mac") or t.get("Color"))]
        seen = set()

        if not valid:
            for card in self.cards.values():
                card.destroy()
            self.cards.clear()
            self.empty.place(relx=0.5, rely=0.5, anchor="center")
            return
        self.empty.place_forget()

        for t in valid:
            key = t.get("mac") or t.get("Color")
            seen.add(key)
            if key not in self.cards:
                self.cards[key] = TiltCard(self.grid_frame, self.style)
            self.cards[key].update_data(t)

        for key in list(self.cards):
            if key not in seen:
                self.cards[key].destroy()
                del self.cards[key]

        self._layout()

    def _layout(self):
        keys = sorted(self.cards)
        width = max(self.grid_frame.winfo_width(), 1)
        cols = max(1, min(len(keys), width // self.style["col_w"])) if width > 1 else 1

        for i in range(12):
            self.grid_frame.columnconfigure(i, weight=0, uniform="")
        for c in range(cols):
            self.grid_frame.columnconfigure(c, weight=1, uniform="cards")

        for idx, key in enumerate(keys):
            r, c = divmod(idx, cols)
            self.cards[key].grid(row=r, column=c, sticky="new", padx=6, pady=6)

    def _on_resize(self, event):
        if event.widget is self and self.cards:
            self._layout()


def main():
    ap = argparse.ArgumentParser(description="Tilt Pi lightweight Tkinter dashboard")
    ap.add_argument("--url", default=DEFAULT_URL,
                    help=f"Node-RED endpoint (default: {DEFAULT_URL})")
    ap.add_argument("--interval", type=float, default=DEFAULT_INTERVAL,
                    help=f"seconds between refreshes (default: {DEFAULT_INTERVAL})")
    ap.add_argument("--windowed", action="store_true",
                    help="start in a window instead of fullscreen")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--compact", action="store_const", dest="layout", const="compact",
                      help="force the compact layout")
    mode.add_argument("--full", action="store_const", dest="layout", const="full",
                      help="force the full 1080p layout")
    ap.set_defaults(layout=None)  # None = auto-select from screen height
    args = ap.parse_args()

    app = Dashboard(args.url, args.interval, fullscreen=not args.windowed,
                    layout=args.layout)
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.close()


if __name__ == "__main__":
    main()
