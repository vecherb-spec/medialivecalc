# Webhook для входящих заявок в калькулятор

Этот проект теперь умеет принимать JSON-заявки и загружать их в интерфейс калькулятора.

## 1) Запуск webhook-сервиса

```bash
python incoming_webhook.py
```

По умолчанию сервис слушает порт `8787` и доступен по:

- `GET /health` — проверка, что сервис работает
- `POST /incoming` — приём JSON-заявки

Файлы заявок сохраняются в папку `incoming_requests/` рядом с `app.py`.

## 2) Пример запроса

```bash
curl -X POST "http://localhost:8787/incoming" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "lead-001",
    "project_name": "ТРЦ Атриум, входная группа",
    "client_name": "ООО Ромашка",
    "width_mm": 3840,
    "height_mm": 2240,
    "env": "Indoor",
    "mount_type": "Монолитный (Магниты/Профиль)",
    "margin_percent": 30,
    "logistics_rub": 20000,
    "installation_rub": 100000,
    "display_currency": "RUB",
    "vat_mode": "С НДС 22%"
  }'
```

## 3) Настройка Make

В Make (scenario):

1. Модуль источника (форма/CRM/бот) формирует JSON.
2. HTTP module → **Make a request**
   - Method: `POST`
   - URL: `http://<ваш-сервер>:8787/incoming`
   - Headers: `Content-Type: application/json`
   - Body type: Raw → JSON
3. Передайте нужные поля из заявки.

После этого в калькуляторе (сайдбар):

- блок **«📥 Входящие заявки»**
- выбрать заявку
- кнопка **«В расчёт»** — подставляет значения в форму.

## Поддерживаемые поля (основные)

- `project_name` / `project`
- `client_name` / `client`
- `width_mm`, `height_mm`
- `env` (`Indoor`/`Outdoor`)
- `mount_type` (`Монолитный (Магниты/Профиль)` / `В кабинетах`)
- `margin_percent`
- `logistics_rub`, `installation_rub`
- `display_currency` (`RUB`/`USD`)
- `vat_mode` (`С НДС 22%`/`Без НДС`) или `vat_enabled` (`true`/`false`)
- `exchange_rate`
- `module_name`

Также можно прислать полный state калькулятора в одном из форматов:

- `{"state": {...}}`
- `{"calc_state": {...}}`
- или просто плоский JSON с ключами `st.session_state`.
