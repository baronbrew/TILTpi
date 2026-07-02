# Tilt Pi Local Dashboard

A lightweight native dashboard that shows live Tilt readings on a monitor
plugged directly into the Raspberry Pi. It reads from the Node-RED flow's
`/macid/all` HTTP endpoint and draws with Tkinter — **no Chromium, no browser**
— so it runs comfortably on a Pi Zero W or any 512 MB Pi where the
`node-red-dashboard` `/ui` page is too heavy.

It's styled to mirror the Node-RED dashboard `:1880/ui` page — same dark theme
(`#111` page, gray toolbar, `#333` cards) and the same Tilt card layout
(full-width color bar, `SG/Concentration … (pre-calibrated)` + big value + fill
bar, temperature likewise, monospace `Received N seconds ago … dBm` footer) —
so it reads as a drop-in replacement for that screen.

## What it shows

One tile per Tilt currently in range (keyed by MAC), each with:

- Beer name and Tilt color strip (with a short MAC tail when *Identify by MAC*
  is on)
- **Gravity** — the calibrated display value (`ferm`, plus `°P`/`°Bx` if you've
  switched units) with a fill bar
- **Temperature** — calibrated `displayTemp` with a fill bar
- Footer: how long ago the reading arrived and the signal strength (dBm), with a
  `⚠ STALE` flag if a Tilt hasn't reported in over a minute

The toolbar shows live/offline state and the Tilt count, plus a
`📱 Settings:` web address for the full Node-RED dashboard — open it on a phone
on the same network to change settings, start logging, switch units, etc. The
address is derived from `--url`; when that points at `localhost` it is shown as
the Pi's own hostname (e.g. `http://tiltpi.local:1880/ui`) so a phone can reach
it.

## Requirements

Python 3 and Tkinter (standard library — nothing to `pip install`). On
Raspberry Pi OS, Tkinter comes from the `python3-tk` package:

```bash
sudo apt-get install -y python3-tk
```

## Run

On the Tilt Pi itself (fetches from the local Node-RED):

```bash
python3 tiltpi_dashboard.py
```

During development, point it at another Pi and run in a window:

```bash
python3 tiltpi_dashboard.py --windowed --url http://tiltpi-office:1880/macid/all
```

### Options

| Flag / env var | Default | Meaning |
| --- | --- | --- |
| `--url` / `TILTPI_URL` | `http://localhost:1880/macid/all` | Node-RED data endpoint |
| `--interval` / `TILTPI_INTERVAL` | `5` | seconds between refreshes |
| `--windowed` | off (fullscreen) | start in a window instead of fullscreen |
| `--compact` | auto | force the compact layout |
| `--full` | auto | force the full 1080p layout |

## Layouts

The dashboard is designed for a **1080p** monitor, where it shows large, bold
stacked gravity and temperature readings. On any screen **shorter than 1080p**
it automatically switches to a **compact layout** — gravity and temperature
sit side-by-side with smaller type and thinner bars, so each card is about half
as tall and many more fit without scrolling. Override the automatic choice with
`--full` or `--compact`.

### Keys

- `F11` or `f` — toggle fullscreen
- `Esc` or `q` — quit

## Start automatically on boot

Tkinter needs an X session, so autostart it from the desktop. On Raspberry Pi
OS with the LXDE desktop, add a line to the autostart file:

```bash
mkdir -p ~/.config/lxsession/LXDE-pi
echo "@python3 /home/pi/TILTpi/dashboard/tiltpi_dashboard.py" \
  >> ~/.config/lxsession/LXDE-pi/autostart
```

Reboot and the dashboard opens fullscreen on the attached monitor. The Node-RED
`/ui` page still works from any browser on the network — this is just a
lightweight local display for the Pi's own screen.

## Notes

- The dashboard keeps the last good reading on screen if Node-RED briefly
  becomes unreachable; the header switches to `● offline` with the error.
- Networking happens on a background thread, so the UI never freezes while
  fetching.
