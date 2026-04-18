import logging
import sys
import time
from datetime import datetime
from typing import Callable, Optional

import serial

from config import load_config
from storage import init_db, insert_sample

log = logging.getLogger("serial_reader")

Sample = Callable[[datetime, Optional[int], Optional[int]], None]


def parse_fields(line: str) -> dict:
    fields = {}
    for part in line.replace(";", ",").split(","):
        if ":" in part:
            key, _, value = part.partition(":")
            fields[key.strip().lower()] = value.strip()
    return fields


def _extract(fields: dict):
    analog = fields.get("gas")
    digital = None
    for key in ("gas_digital", "digital", "gas_d"):
        if key in fields:
            digital = fields[key]
            break
    return analog, digital


def read_serial(port: str, baud_rate: int, on_sample: Sample,
                reconnect_delay: float = 2.0) -> None:
    analog = None
    digital = None
    while True:
        try:
            ser = serial.Serial(port, baud_rate, timeout=1)
            log.info("Opened %s @ %d", port, baud_rate)
        except serial.SerialException as e:
            log.error("Error opening %s: %s — retrying in %.1fs", port, e, reconnect_delay)
            time.sleep(reconnect_delay)
            continue

        try:
            while True:
                raw = ser.readline().decode("ascii", errors="replace").strip()
                if not raw:
                    continue
                fields = parse_fields(raw)
                a, d = _extract(fields)
                if a is not None:
                    analog = int(a)
                if d is not None:
                    digital = int(d)
                if analog is None and digital is None:
                    continue
                on_sample(datetime.now(), analog, digital)
        except serial.SerialException as e:
            log.warning("Serial error: %s — reconnecting", e)
        finally:
            try:
                ser.close()
            except Exception:
                pass
        time.sleep(reconnect_delay)


def _print_sample(ts, analog, digital):
    print(f"{ts:%Y-%m-%d %H:%M:%S}  Gas analog: {analog}  Gas digital: {digital}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    cfg = load_config()
    db_path = cfg["storage"]["db_path"]
    init_db(db_path)

    callbacks = [_print_sample, lambda ts, a, d: insert_sample(db_path, ts, a, d)]

    if cfg.get("telegram", {}).get("enabled"):
        try:
            from telegram_bot import AlertDispatcher
            dispatcher = AlertDispatcher(cfg)
            callbacks.append(dispatcher.handle_sample)
        except Exception as e:
            log.warning("Telegram disabled: %s", e)

    def on_sample(ts, a, d):
        for cb in callbacks:
            try:
                cb(ts, a, d)
            except Exception as e:
                log.exception("callback failed: %s", e)

    try:
        read_serial(
            cfg["serial"]["port"],
            cfg["serial"]["baud_rate"],
            on_sample,
            cfg["serial"].get("reconnect_delay", 2.0),
        )
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
