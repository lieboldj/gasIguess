# 🏠 Smart Home — Gas Sensor Dashboard

> **Built at WoHa! Women's Hackathon 2026 · Hamburg, 18 April 2026**
> IoT track · Smart Minihome challenge

***

In one day at Hamburg's SPACE venue, our team built a fully working smart home gas sensor system:
a BBC micro:bit reads analog and digital gas sensor signals, streams them over USB serial to a Python backend,
stores every sample in SQLite, and surfaces everything through a live Streamlit dashboard. Zero cloud dependencies, runs fully local.

***

## Demo proof

The dashboard auto-refreshes in the browser while `serial_reader.py` feeds live readings into the database.
Below is a typical view during the hackathon demo:

- **Analog gauge** — raw ADC value from P0 (0–1023)
- **Digital status** — HIGH / LOW from P1 (hardware trip wire)
- **Time-series chart** — rolling window of the last N samples

***

## Architecture

```
micro:bit ─(USB serial)→ serial_reader.py ──► SQLite (gas_sensor.db)
                                                     ▲
                                dashboard.py (Streamlit) ── reads SQLite
```

The reader and dashboard are independent processes — the dashboard never blocks the sensor loop,
and the database acts as the shared state.

***

## micro:bit Firmware

Flash the following MicroPython snippet to the micro:bit. It emits one CSV-style line per second over USB serial:

```python
from microbit import *

while True:
    print("gas:{},gas_digital:{}".format(pin0.read_analog(), pin1.read_digital()))
    sleep(1000)
```

- **P0** — analog signal (0–1023), sensitive proportional reading
- **P1** — digital signal (0 or 1), hardware threshold trip from the sensor module

***

## Setup

### Requirements

```bash
pip install -r requirements.txt
```

### Configuration

Edit `config.yaml` before starting:

```yaml
serial:
  port: /dev/ttyACM0        # Windows: COM3, macOS: /dev/tty.usbmodem*
  baud: 115200

thresholds:
  alert: 400                # analog value that triggers an alert
  consecutive: 3            # number of consecutive samples before alerting
  cooldown: 60              # seconds between repeat alerts
```

***

## Running

### Manual (two terminals)

```bash
# Terminal 1 — serial reader (also prints to stdout for live debugging)
python serial_reader.py

# Terminal 2 — Streamlit dashboard at http://localhost:8501
streamlit run dashboard.py
```

### Via systemd (persistent background service)

```bash
cp systemd/gas-reader.service   ~/.config/systemd/user/
cp systemd/gas-dashboard.service ~/.config/systemd/user/

systemctl --user enable --now gas-reader gas-dashboard
```

The units restart automatically on failure and survive reboots.

***

### Alert Rules

| Trigger | Condition |
|---|---|
| **Digital trip** | P1 transitions 0 → 1 |
| **Analog over threshold** | `analog ≥ thresholds.alert` for `thresholds.consecutive` samples in a row |
| **Cooldown** | Repeat alerts suppressed for `thresholds.cooldown` seconds |

***

## File Reference

| File | Purpose |
|---|---|
| `config.yaml` | Runtime configuration (port, thresholds) |
| `config.py` | Config loader and validation |
| `serial_reader.py` | Serial reader, parser, and sample dispatcher |
| `storage.py` | SQLite persistence layer |
| `dashboard.py` | Streamlit live dashboard |
| `test_script.py` | Minimal legacy reader for quick hardware checks |
| `systemd/` | Systemd user service units |

***

## Hackathon Context

This project was built during the **WoHa! Women's Hackathon 2026**,
the third edition of Hamburg's free, hands-on hackathon for women and non-binary people interested in tech.
The event took place on **18 April 2026, 9:30–16:00** at **SPACE Hamburg, Am Sandtorkai 27**.

WoHa! is recognised by the EU project *Connecting Women in Digital* as a best-practice format.
Our team worked in the **Internet of Things — Smart Minihome** track, which challenged participants to
bring a miniature smart home to life using sensors, microcontrollers, and custom code.

**Jeanine Liebold** guided one subgroup from hardware wiring through
firmware flashing to a fully functional live dashboard — all within the six-hour hackathon slot.

***

*Participants: bring your own laptop. No cloud account needed. Runs entirely on-device.*

