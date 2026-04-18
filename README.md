# Smart Home — Gas Sensor

Live dashboard + Telegram alerts for a gas sensor wired to a BBC micro:bit
(analog on P0, digital on P1).

## Architecture

```
micro:bit ─(USB serial)→ serial_reader.py ─┬─► SQLite (gas_sensor.db)
                                           └─► AlertDispatcher ─► Telegram
                                                     ▲
                                dashboard.py (Streamlit) ── reads SQLite
```

## Setup

```bash
pip install -r requirements.txt
```

Edit `config.yaml` — serial port, thresholds, and (optional) Telegram token/chat id.

## Running

Two processes:

```bash
# terminal 1 — reader (also prints to stdout)
python serial_reader.py

# terminal 2 — dashboard at http://localhost:8501
streamlit run dashboard.py
```

Or via systemd — copy the units in `systemd/` to `~/.config/systemd/user/` and
`systemctl --user enable --now gas-reader gas-dashboard`.

## micro:bit firmware

The device should emit one line per sample over serial, e.g.:

```python
from microbit import *
while True:
    print("gas:{},gas_digital:{}".format(pin0.read_analog(), pin1.read_digital()))
    sleep(1000)
```

## Telegram alerts

1. Create a bot via [@BotFather](https://t.me/BotFather), copy the token.
2. Message your bot once, then find your chat id via
   `https://api.telegram.org/bot<TOKEN>/getUpdates`.
3. Fill `telegram.token` / `telegram.chat_id` in `config.yaml` and set
   `telegram.enabled: true`.

Alert rules:
- **Digital trip**: P1 transitions 0→1.
- **Analog over threshold**: `analog ≥ thresholds.alert` for
  `thresholds.consecutive` samples in a row.
- `thresholds.cooldown` (seconds) throttles repeat alerts.

## Files

| File                | Purpose                                           |
| ------------------- | ------------------------------------------------- |
| `config.yaml`       | Runtime config                                    |
| `config.py`         | Config loader                                     |
| `serial_reader.py`  | Serial reader + sample dispatcher                 |
| `storage.py`        | SQLite persistence                                |
| `dashboard.py`      | Streamlit UI                                      |
| `telegram_bot.py`   | Alert dispatcher                                  |
| `test_script.py`    | Legacy minimal reader (kept for quick checks)     |
| `systemd/`          | User service units                                |
