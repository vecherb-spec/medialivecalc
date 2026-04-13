#!/usr/bin/env python3
from __future__ import annotations

import datetime
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, make_response, request, send_from_directory

APP = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
INCOMING_DIR = BASE_DIR / "incoming_requests"
QUIZ_DIR = BASE_DIR / "quiz"
ALLOWED_ORIGINS = {
    "https://medialive.ru",
    "https://www.medialive.ru",
    "https://calc.medialive.ru",
    "https://quiz.medialive.ru",
}


def _safe_part(value: str) -> str:
    sanitized = re.sub(r"[^\w\-.()\s\u0400-\u04FF]", "_", (value or "").strip(), flags=re.UNICODE)
    sanitized = re.sub(r"\s+", "_", sanitized).strip("_")
    return sanitized[:80] or "request"


def _normalize_payload(payload: Any) -> dict:
    if isinstance(payload, dict):
        return payload
    return {"raw_payload": payload}


def _with_cors(resp):
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return resp


@APP.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@APP.route("/quiz", methods=["GET"])
@APP.route("/quiz/", methods=["GET"])
def quiz_page():
    return send_from_directory(QUIZ_DIR, "index.html")


@APP.route("/quiz/<path:filename>", methods=["GET"])
def quiz_assets(filename: str):
    return send_from_directory(QUIZ_DIR, filename)


@APP.route("/incoming", methods=["POST", "OPTIONS"])
def incoming():
    if request.method == "OPTIONS":
        return _with_cors(make_response("", 204))

    payload = request.get_json(silent=True)
    if payload is None:
        return _with_cors(jsonify({"ok": False, "error": "invalid_or_empty_json"})), 400

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

    return _with_cors(
        jsonify(
            {
                "ok": True,
                "saved_to": str(target_path),
                "received_at": record["received_at"],
            }
        )
    )


if __name__ == "__main__":
    port = int(os.environ.get("WEBHOOK_PORT", "8787"))
    APP.run(host="0.0.0.0", port=port, debug=False)
