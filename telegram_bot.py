"""Telegram alert dispatcher for gas sensor events.

Uses simple HTTP calls to the Bot API — no external dependency needed.
"""
import logging
import time
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from i18n import t

log = logging.getLogger("telegram_bot")


def send_message(token: str, chat_id: str, text: str) -> bool:
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urlencode({"chat_id": chat_id, "text": text}).encode()
    try:
        with urlopen(Request(url, data=data), timeout=5) as resp:
            return resp.status == 200
    except Exception as e:
        log.warning("Telegram send failed: %s", e)
        return False


class AlertDispatcher:
    """Watches samples and emits debounced, cooldown-aware Telegram alerts."""

    def __init__(self, cfg: dict):
        tg = cfg.get("telegram", {})
        th = cfg.get("thresholds", {})
        self.token = tg.get("token", "")
        self.chat_id = tg.get("chat_id", "")
        self.lang = cfg.get("language", "de")
        self.warn = th.get("warn", 400)
        self.alert = th.get("alert", 600)
        self.consecutive = th.get("consecutive", 3)
        self.cooldown = th.get("cooldown", 300)

        self._over_count = 0
        self._last_digital = None
        self._last_alert_ts = 0.0

    def _can_fire(self) -> bool:
        return time.time() - self._last_alert_ts >= self.cooldown

    def _fire(self, text: str) -> None:
        if send_message(self.token, self.chat_id, text):
            self._last_alert_ts = time.time()
            log.info("Alert sent: %s", text)

    def handle_sample(self, ts: datetime, analog, digital) -> None:
        stamp = ts.strftime("%Y-%m-%d %H:%M:%S")

        if digital is not None:
            if self._last_digital == 1 and digital == 0 and self._can_fire():
                self._fire(t(self.lang, "alert_digital", ts=stamp, analog=analog))
            self._last_digital = digital

        if analog is not None:
            if analog >= self.alert:
                self._over_count += 1
            else:
                self._over_count = 0
            if self._over_count >= self.consecutive and self._can_fire():
                self._fire(t(self.lang, "alert_analog", analog=analog,
                             threshold=self.alert, count=self._over_count, ts=stamp))
                self._over_count = 0
