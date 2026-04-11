#!/usr/bin/env python3
from __future__ import annotations

import datetime
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request

APP = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
INCOMING_DIR = BASE_DIR / "incoming_requests"


def _safe_part(value: str) -> str:
    sanitized = re.sub(r"[^\w\-.()\s\u0400-\u04FF]", "_", (value or "").strip(), flags=re.UNICODE)
    sanitized = re.sub(r"\s+", "_", sanitized).strip("_")
    return sanitized[:80] or "request"


def _normalize_payload(payload: Any) -> dict:
    if isinstance(payload, dict):
        return payload
    return {"raw_payload": payload}


@APP.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@APP.route("/incoming", methods=["POST"])
def incoming():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"ok": False, "error": "invalid_or_empty_json"}), 400

    normalized = _normalize_payload(payload)
    record = {
        "received_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "source_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "data": normalized,
    }

    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    req_id = str(
        normalized.get("request_id")
        or normalized.get("id")
        or normalized.get("lead_id")
        or ""
    )
    project = str(
        normalized.get("project_name")
        or normalized.get("project")
        or normalized.get("client")
        or ""
    )
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = (
        f"{ts}_{_safe_part(project)}_{_safe_part(req_id)}_{uuid.uuid4().hex[:6]}.json"
    )
    target_path = INCOMING_DIR / filename
    target_path.write_text(
        json.dumps(
            {
                "received_at": record["received_at"],
                "source_ip": record["source_ip"],
                "payload": normalized,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return jsonify(
        {
            "ok": True,
            "saved_to": str(target_path),
            "received_at": record["received_at"],
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("WEBHOOK_PORT", "8787"))
    APP.run(host="0.0.0.0", port=port, debug=False)
