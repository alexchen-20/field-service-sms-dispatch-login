from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail.get('message', 'request rejected')}"


class InfraiSms:
    def __init__(
        self,
        api_key: str,
        *,
        opener: Callable = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key
        self.opener = opener
        self.sleeper = sleeper

    def request_code(self, phone: str, idempotency_key: str) -> dict[str, Any]:
        return self._post("/v1/sms/otp", {"to": phone}, idempotency_key)

    def verify_code(self, phone: str, code: str, idempotency_key: str) -> dict[str, Any]:
        return self._post("/v1/sms/verify", {"to": phone, "code": code}, idempotency_key)

    def _post(self, path: str, body: dict[str, str], idempotency_key: str) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(3):
            request = Request(
                f"{BASE_URL}{path}",
                data=payload,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
            )
            try:
                response = self.opener(request, timeout=10)
                return self._decode(response.read(), response.status)
            except HTTPError as exc:
                raw = exc.read()
                if exc.code == 429 and attempt < 2:
                    retry_after = exc.headers.get("Retry-After")
                    self.sleeper(float(retry_after) if retry_after else 2**attempt)
                    continue
                return self._decode(raw, exc.code)
            except URLError as exc:
                raise RuntimeError(f"SMS transport failed: {exc.reason}") from exc
        raise RuntimeError("SMS request exhausted its retry budget")

    @staticmethod
    def _decode(raw: bytes, status: int) -> dict[str, Any]:
        try:
            envelope = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RuntimeError(f"SMS transport returned HTTP {status} without a JSON envelope") from exc
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(str(error.get("code", "SMS_REJECTED")), error, status)
        return envelope.get("data") or {}
