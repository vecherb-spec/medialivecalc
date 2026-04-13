# Webhook для входящих заявок в калькулятор

Этот проект умеет:

- принимать JSON-заявки и загружать их в интерфейс калькулятора;
- отдавать готовую страницу квиза (`/quiz`) для встраивания на сайт.

## 1) Запуск webhook-сервиса

```bash
python incoming_webhook.py
```

По умолчанию сервис слушает порт `8787` и доступен по:

- `GET /health` — проверка, что сервис работает
- `POST /incoming` — приём JSON-заявки
- `GET /quiz` — страница квиза (frontend)

Файлы заявок сохраняются в папку `incoming_requests/` рядом с `app.py`.

## 1.1) Встраиваемый квиз

Готовый квиз лежит в `quiz/index.html` и отдается Flask-роутом:

- `http://<ваш-сервер>:8787/quiz`

Поддержано:

- пошаговая форма (6 шагов),
- кнопки "Назад"/"Далее",
- progress bar,
- зависимые шаги (ветвление),
- сохранение состояния при переходах и перезагрузке (localStorage),
- адаптивная верстка под мобильные.

> Размеры на шаге "Размеры" для непрокатных экранов автоматически округляются до ближайших значений, кратных `320x160 мм`.

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

## 4) Встройка квиза в Tilda (iframe)

Рекомендуемый способ — iframe в HTML-блоке Tilda:

```html
<iframe
  src="https://calc.medialive.ru/quiz"
  style="width:100%;height:820px;border:0;border-radius:12px;"
  loading="lazy">
</iframe>
```

### Nginx (важно)

Чтобы маршрут `/quiz` шел в Flask webhook-сервис, добавьте в конфиг сайта:

```nginx
location /quiz {
    proxy_pass http://127.0.0.1:8787/quiz;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

Если нужны ассеты `/quiz/...`, удобнее сделать:

```nginx
location /quiz/ {
    proxy_pass http://127.0.0.1:8787/quiz/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

Для домена `quiz.medialive.ru` также добавьте проксирование webhook, чтобы квиз мог отправлять в same-origin fallback `/incoming`:

```nginx
location /incoming {
    proxy_pass http://127.0.0.1:8787/incoming;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

## 5) Уведомления в Telegram (опционально)

Webhook умеет отправлять каждую новую заявку в Telegram-чат.

Нужны переменные окружения:

- `TELEGRAM_BOT_TOKEN` — токен вашего бота (`123456:ABC...`)
- `TELEGRAM_CHAT_ID` — ID чата/группы/канала
- `TELEGRAM_THREAD_ID` — (опционально) ID топика в группе с Topics

Пример для systemd (`medialive-webhook.service`):

```ini
Environment=TELEGRAM_BOT_TOKEN=123456789:AA...
Environment=TELEGRAM_CHAT_ID=-1001234567890
Environment=TELEGRAM_THREAD_ID=42
```

После изменения:

```bash
sudo systemctl daemon-reload
sudo systemctl restart medialive-webhook
sudo systemctl status medialive-webhook --no-pager -l
```

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
