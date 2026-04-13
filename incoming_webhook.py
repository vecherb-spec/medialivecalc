#!/usr/bin/env python3
from __future__ import annotations

import datetime
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any
import urllib.request
import urllib.error

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


def _to_text(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _extract_phone(raw: str) -> str:
    phone = re.sub(r"[^\d+]", "", raw or "")
    if phone.startswith("8") and len(phone) == 11:
        phone = "+7" + phone[1:]
    return phone


def _contact_html(contact_method: str, contact_value: str) -> str:
    method = (contact_method or "").strip().lower()
    value = (contact_value or "").strip()
    escaped = _escape_html(value)
    if not value:
        return "—"

    if "email" in method and "@" in value:
        return f'<a href="mailto:{escaped}">{escaped}</a>'

    if "telegram" in method:
        username = value.lstrip("@")
        if re.fullmatch(r"[A-Za-z0-9_]{4,}", username):
            safe_user = _escape_html(username)
            return f'<a href="https://t.me/{safe_user}">@{safe_user}</a>'

    if any(x in method for x in ("телефон", "звонок", "whatsapp", "mobile")):
        phone = _extract_phone(value)
        if phone:
            safe_phone = _escape_html(phone)
            return f'<a href="tel:{safe_phone}">{escaped}</a>'

    return escaped


def _as_float(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _telegram_send_message(token: str, body: dict[str, Any]) -> tuple[bool, str]:
    req = urllib.request.Request(
        url=f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
            if data.get("ok") is True:
                return True, "ok"
            return False, f"telegram_api_not_ok: {raw[:300]}"
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            detail = str(exc)
        return False, f"http_{exc.code}: {detail[:300]}"
    except (urllib.error.URLError, TimeoutError) as exc:
        return False, str(exc)


def _notify_telegram(payload: dict, record: dict, saved_to: Path) -> tuple[bool, str]:
    token = _to_text(os.environ.get("TELEGRAM_BOT_TOKEN"))
    chat_id = _to_text(os.environ.get("TELEGRAM_CHAT_ID"))
    if not token or not chat_id:
        return False, "disabled_missing_env"

    req_id = _to_text(payload.get("request_id") or payload.get("id") or payload.get("lead_id")) or "—"
    project = _to_text(payload.get("project_name") or payload.get("project")) or "—"
    client_name = _to_text(
        payload.get("client_name") or payload.get("name") or payload.get("client")
    ) or "—"
    city = _to_text(payload.get("city")) or "—"
    screen_type = _to_text(payload.get("type") or payload.get("screenType")) or "—"
    subtype = _to_text(payload.get("subtype")) or "—"
    pixel = _to_text(payload.get("pixel_pitch") or payload.get("pixelPitch")) or "—"
    installation = _to_text(payload.get("installation_choice") or payload.get("installation_note")) or "—"
    contact_method = _to_text(payload.get("contact_method")) or "—"
    contact_value = _to_text(payload.get("contact_value") or payload.get("phone") or payload.get("client_name")) or "—"
    contact_html = _contact_html(contact_method, contact_value)
    width = _to_text(payload.get("width_mm"))
    height = _to_text(payload.get("height_mm"))
    size = f"{width}×{height} мм" if width and height else "—"
    source = _to_text(payload.get("source") or payload.get("lead_source")) or "quiz/webhook"

    area = "—"
    w_float = _as_float(payload.get("width_mm"))
    h_float = _as_float(payload.get("height_mm"))
    if w_float and h_float and w_float > 0 and h_float > 0:
        area = f"{(w_float * h_float) / 1_000_000:.2f} м²"

    lines = [
        "🆕 <b>Новая заявка Medialive</b>",
        "",
        f"👤 <b>Клиент:</b> {_escape_html(client_name)}",
        f"📞 <b>Контакт:</b> {contact_html}",
        f"🏙️ <b>Город:</b> {_escape_html(city)}",
        "",
        f"🖥️ <b>Экран:</b> {_escape_html(screen_type)} / {_escape_html(subtype)}",
        f"📐 <b>Размер:</b> {_escape_html(size)}",
        f"📊 <b>Площадь:</b> {_escape_html(area)}",
        f"🔎 <b>Шаг пикселя:</b> {_escape_html(pixel)}",
        f"🛠️ <b>Монтаж:</b> {_escape_html(installation)}",
        "",
        f"🆔 <b>ID:</b> <code>{_escape_html(req_id)}</code>",
        f"📡 <b>Источник:</b> {_escape_html(source)}",
        f"🕒 <b>Время:</b> {_escape_html(_to_text(record.get('received_at')))}",
    ]
    text = "\n".join(lines)
    plain_text = (
        "Новая заявка Medialive\n"
        f"Клиент: {client_name}\n"
        f"Контакт: {contact_method} — {contact_value}\n"
        f"Город: {city}\n"
        "\n"
        f"Экран: {screen_type} / {subtype}\n"
        f"Размер: {size}\n"
        f"Площадь: {area}\n"
        f"Шаг пикселя: {pixel}\n"
        f"Монтаж: {installation}\n"
        "\n"
        f"ID: {req_id}\n"
        f"Проект: {project}\n"
        f"Источник: {source}\n"
        f"Время: {_to_text(record.get('received_at'))}"
    )

    body: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    thread_id = _to_text(os.environ.get("TELEGRAM_THREAD_ID"))
    if thread_id:
        try:
            body["message_thread_id"] = int(thread_id)
        except ValueError:
            pass

    ok, note = _telegram_send_message(token, body)
    if not ok:
        # Fallback: plain text without parse_mode (some chats reject HTML entities/format)
        fallback_body = {
            "chat_id": chat_id,
            "text": plain_text,
            "disable_web_page_preview": True,
        }
        if "message_thread_id" in body:
            fallback_body["message_thread_id"] = body["message_thread_id"]
        ok2, note2 = _telegram_send_message(token, fallback_body)
        if ok2:
            print(
                f"[telegram_notify] fallback_plain_text_ok saved={saved_to} first_error={note}",
                flush=True,
            )
            return True, "fallback_plain_text_ok"
        print(
            f"[telegram_notify] failed saved={saved_to} html_error={note}; plain_error={note2}",
            flush=True,
        )
        return False, note2

    print(f"[telegram_notify] ok saved={saved_to}", flush=True)
    return True, note


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
    tg_ok, tg_note = _notify_telegram(normalized, record, target_path)

    return _with_cors(
        jsonify(
            {
                "ok": True,
                "saved_to": str(target_path),
                "received_at": record["received_at"],
                "telegram_notified": tg_ok,
                "telegram_note": tg_note,
            }
        )
    )


if __name__ == "__main__":
    port = int(os.environ.get("WEBHOOK_PORT", "8787"))
    APP.run(host="0.0.0.0", port=port, debug=False)
