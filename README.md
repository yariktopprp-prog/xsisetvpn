# xsiset vpn

Сайт VPN-сервиса: тёмная тема по умолчанию, светлая по кнопке, один синий акцент,
крупная типографика. Это не статика: Flask-бэкенд сам создаёт заказы, выставляет счёт
в CryptoBot или Platega, проверяет оплату и выдаёт VLESS-ключ через панель 3x-ui.
Пользователь скачивает ключ файлом `.txt`.

- Бот (пробный период и поддержка): [@xsisetvpnbot](https://t.me/xsisetvpnbot)
- Серверы: Нидерланды (1), Швеция (2), Германия (1), обход белых списков (1) — всего 5
- Цены: 1 мес — 100 ₽, 3 мес — 270 ₽, 6 мес — 500 ₽, 12 мес — 900 ₽
- Оплата на сайте: CryptoBot (USDT, TRX, TON) и Platega (карта, СБП)
- Пробный период выдаётся **только в Telegram-боте** — на сайте это указано

## Что умеет

- покупка без аккаунта: заказ получает одноразовый `access_token`, ключ доступен по нему;
- аккаунт по почте и паролю (pbkdf2) или через Telegram Login Widget;
- список купленных ключей и повторное скачивание `.txt`;
- обязательное согласие на обработку персональных данных (`consent_at`, `consent_ip`,
  `consent_version`);
- идемпотентная выдача ключа: один UUID и один `subId` на заказ, клиент добавляется
  во все inbound'ы, при частичной ошибке — откат;
- фоновый сверщик оплат (`XSISET_RECONCILE_SECONDS`), плюс поллинг из браузера.

## Структура

```
xsisetvpn/
├── index.html          страница: тарифы, оформление, оплата, ключ, аккаунт
├── privacy.html        политика обработки персональных данных
├── style.css           токены, темы, компоненты
├── script.js           RU/EN, тема, меню, аккаунт, заказ и оплата
├── 404.html
├── robots.txt
└── server/
    ├── app.py          Flask: статика, API, фоновая сверка оплат
    ├── config.py       тарифы, окружение, .env
    ├── db.py           SQLite: пользователи, заказы, события
    ├── auth.py         пароли, сессии, проверка Telegram Login Widget
    ├── payments.py     CryptoBot и Platega: счёт и статус
    ├── panel.py        3x-ui: создание и удаление VLESS-клиентов
    ├── keyfile.py      текст файла с ключом
    ├── requirements.txt
    ├── .env.example
    └── data/           SQLite и session.key, в git не попадают
```

## Локальный запуск

```powershell
cd D:\course\web\xsisetvpn\server
pip install -r requirements.txt
$env:XSISET_PANEL_MODE = "dry"   # заглушка вместо записи в боевую панель
$env:XSISET_DEMO = "1"           # кнопка «Демо-оплата»
python app.py
```

Открыть <http://127.0.0.1:8124/>. Сайт и API отдаёт один процесс.

`XSISET_PANEL_MODE=dry` не трогает 3x-ui: ключ получает ссылку вида
`https://panel.example/sub/dry-...`. Демо-оплата работает только при `XSISET_DEMO=1`
и только для локальных запросов.

## Как проходит покупка

1. Пользователь выбирает тариф. Форма оформления предлагает режим «Без аккаунта»,
   вход по почте или через Telegram.
2. `POST /api/orders` создаёт заказ в SQLite (`pending`) и сразу создаёт счёт:
   - CryptoBot: `createInvoice` в рублях с `accepted_assets` (USDT/TRX/TON);
   - Platega: `POST /v2/transaction/process` (карта, СБП).
3. Браузер показывает ссылку на оплату и опрашивает `GET /api/orders/<id>` каждые 4 секунды.
4. Сайт сам сверяет статус с провайдером. `paid/success/confirmed/completed` → заказ
   `paid`; `failed/canceled/expired/declined` → `failed`. Вебхуки не используются.
5. После `paid` сайт создаёт VLESS-клиента в панели 3x-ui, сохраняет `subId`,
   ссылку-подписку и срок действия.
6. Пользователь скачивает `xsiset-vpn-<order_id>.txt`: внутри ссылка-подписка и
   инструкция. Ключ можно скопировать и с экрана.

Заказ живёт `XSISET_ORDER_TTL_HOURS` (по умолчанию 24 часа), затем становится `expired`.
Статусы: `pending` → `paid` | `failed` | `expired`. Выдача ключа идемпотентна.

### Анонимная покупка

При создании заказа API возвращает `access_token` (32 hex) **один раз**. Только с ним
(или из сессии владельца) можно смотреть статус, отменять заказ и скачивать ключ.
Токен хранится в `localStorage` браузера, чтобы пережить перезагрузку.

### Выдача ключа

`panel.create_client()`:

- генерирует UUID и `subId`;
- добавляет клиента в inbound'ы `XSISET_PANEL_INBOUNDS` (по умолчанию `5,11,13,16,17`);
- при ошибке на любом inbound'е удаляет уже добавленного клиента из предыдущих;
- запросы к панели повторяются 3 раза с паузой (хост периодически отвечает таймаутом).

Ссылка-подписка: `XSISET_PANEL_SUB_BASE` + `/` + `subId` + `#XsisetVPN`.

## API

| Метод | Путь | Что делает |
|---|---|---|
| GET | `/api/health` | состояние панели, платёжных провайдеров, демо-режима |
| GET | `/api/plans` | тарифы: месяцы, цена, цена за месяц, экономия |
| POST | `/api/orders` | `{plan_id, method, asset?, consent}` → заказ, `pay_url`, `token` |
| GET | `/api/orders/<id>?token=…` | статус, ссылка на оплату, ключ |
| POST | `/api/orders/<id>/cancel?token=…` | отменить ожидающий заказ |
| POST | `/api/orders/<id>/demo-pay?token=…` | только при `XSISET_DEMO=1` |
| GET | `/api/orders/<id>/key.txt?token=…&lang=ru\|en` | файл с ключом |
| GET | `/api/orders` | заказы текущего аккаунта |
| GET | `/api/auth/me` | текущий пользователь и доступность Telegram-входа |
| POST | `/api/auth/register` | `{email, password, consent}` |
| POST | `/api/auth/login` | `{email, password}` |
| POST | `/api/auth/logout` | завершить сессию |
| GET | `/api/auth/telegram/callback` | редирект от Telegram Login Widget |

Деньги в API — в копейках (`amount`), рядом лежит `price` в рублях.
Ошибки: `{"ok":false,"error":"code"}` с кодом 4xx/5xx.

### Регистрация и вход через Telegram

Почта: email + пароль от 8 символов, пароль хранится как `pbkdf2:sha256`, сессия —
подписанная cookie (`HttpOnly`, `SameSite=Lax`).

Telegram: Login Widget с `data-auth-url=/api/auth/telegram/callback`. Подпись проверяется
как `HMAC-SHA256(SHA256(bot_token), data_check_string)`, `auth_date` не старше суток.
Виджет работает только на домене с HTTPS, который указан в BotFather для бота.

## Настройки

Скопировать `server/.env.example` в `server/.env` и заполнить. Файл не коммитится
и наружу не отдаётся.

| Переменная | По умолчанию | Зачем |
|---|---|---|
| `XSISET_BOT` | `xsisetvpnbot` | имя бота без `@` |
| `XSISET_BOT_TOKEN` | — | проверка подписи Telegram Login Widget |
| `XSISET_CRYPTOPAY_TOKEN` | — | Crypto Pay API |
| `XSISET_CRYPTO_ASSETS` | `USDT,TRX,TON` | доступные монеты |
| `XSISET_PLATEGA_MERCHANT_ID` / `_SECRET` | — | Platega API |
| `XSISET_PANEL_URL` / `_TOKEN` | — | 3x-ui, URL панели и Bearer-токен |
| `XSISET_PANEL_INBOUNDS` | `5,11,13,16,17` | inbound'ы для клиента |
| `XSISET_PANEL_SUB_BASE` | — | база ссылки-подписки |
| `XSISET_PANEL_MODE` | `live` | `dry` — не писать в панель |
| `XSISET_PANEL_VERIFY_TLS` | `true` | проверка TLS панели |
| `XSISET_DEMO` | `0` | демо-оплата, только локально |
| `XSISET_SECRET_KEY` | генерируется | подпись cookie сессии |
| `XSISET_COOKIE_SECURE` | `0` | включить за HTTPS |
| `XSISET_RECONCILE_SECONDS` | `120` | период фоновой сверки, `0` — выключить |
| `XSISET_ORDER_TTL_HOURS` | `24` | срок жизни заказа |
| `XSISET_PAYMENT_TTL_MINUTES` | `60` | срок жизни счёта |
| `XSISET_CONSENT_VERSION` | `2026-11-01` | версия согласия |
| `XSISET_DB` | `server/data/orders.sqlite3` | путь к базе |
| `XSISET_HOST` / `XSISET_PORT` | `127.0.0.1` / `8124` | адрес Flask |

`XSISET_SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`.
Если не задан, ключ создаётся в `server/data/session.key`.

## Прод

Сайт и API живут в одной папке, Flask слушает только loopback.

```bash
sudo mkdir -p /opt/xsisetvpn
sudo rsync -av --delete --exclude 'server/data' --exclude 'server/.env' ./ /opt/xsisetvpn/
cd /opt/xsisetvpn
python3 -m venv .venv && . .venv/bin/activate
pip install -r server/requirements.txt
```

`/etc/systemd/system/xsisetvpn.service`:

```ini
[Unit]
Description=xsiset vpn site and orders API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/xsisetvpn/server
EnvironmentFile=/opt/xsisetvpn/server/.env
ExecStart=/opt/xsisetvpn/.venv/bin/gunicorn -w 2 -b 127.0.0.1:8124 app:app
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/xsisetvpn/server/data

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now xsisetvpn
```

nginx:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name vpn.example.com;

    root /opt/xsisetvpn;
    index index.html;

    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-Frame-Options "DENY" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    client_max_body_size 64k;
    gzip on;
    gzip_min_length 1024;
    gzip_types text/css application/javascript image/svg+xml application/json;

    location = /index.html { expires -1; }
    location ~* \.(css|js)$ { expires 7d; }

    location /api/ {
        proxy_pass http://127.0.0.1:8124;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # политика ПД и статика Flask отдаёт по белому списку
    location = /privacy { proxy_pass http://127.0.0.1:8124; }
    location = /privacy.html { proxy_pass http://127.0.0.1:8124; }

    # код, env и база — не наружу
    location ^~ /server/ { deny all; }
    location ~ /\. { deny all; }

    location / {
        try_files $uri $uri/ =404;
    }

    error_page 404 /404.html;
    location = /404.html { internal; }
}
```

`certbot --nginx -d vpn.example.com`. HTTPS обязателен: без него Telegram Login Widget
не работает, а `XSISET_COOKIE_SECURE` оставлять включённым нельзя.

CSP и остальные заголовки ставит Flask (`app.py`), поэтому в nginx их дублировать не нужно.
Инлайновый скрипт в `index.html` (тема до первой отрисовки) разрешён по хешу
`sha256-KJJarRUqEub4pPAihlLER8GAzKLaKGcd7AV7yMHBvgU=`. Если скрипт меняется — пересчитать:

```python
import base64, hashlib, io, re
html = io.open('index.html', encoding='utf-8').read()
body = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
print('sha256-' + base64.b64encode(hashlib.sha256(body.encode()).digest()).decode())
```

После смены домена добавить его в BotFather: `/setdomain`.

### Бэкап

```bash
sudo -u www-data sqlite3 /opt/xsisetvpn/server/data/orders.sqlite3 \
  ".backup '/var/backups/xsisetvpn-$(date +%F).sqlite3'"
```

В базе пользователи, заказы, события и выданные `subId`. Карточных данных там нет.
Ссылки-подписки остаются рабочими в панели 3x-ui даже при потере базы.

## Безопасность

- Пароли — `pbkdf2:sha256`, сессии — подписанная `HttpOnly` cookie; CSRF-защита — проверка
  `Origin` для всех POST и `SameSite=Lax`.
- Telegram-вход проверяет HMAC-подпись и свежесть `auth_date`.
- Заказ, статус и ключ доступны только владельцу сессии или по случайному `access_token`.
- `POST /api/orders` — 20 заказов с IP за 10 минут; вход/регистрация — 20 попыток за 15 минут.
- ID заказа и токен — случайные (`secrets`), перебор не имеет смысла.
- `server/`, `.env`, база и скрытые файлы наружу не отдаются: статика только по белому списку.
- Демо-оплата отклоняется, если запрос пришёл через прокси (`X-Real-IP`).
- CSP, `nosniff`, `Referrer-Policy`, `X-Frame-Options`, `Permissions-Policy` — из Flask.
- Сайт не принимает и не хранит карточные данные: только идентификатор счёта у провайдера.
- Согласие на обработку ПД фиксируется с IP и версией документа; политика — `privacy.html`.

## Дизайн

Общие токены: `--bg #000`, карточки `#161618`, чипы `#2e2e30`, синий `#0071e3`.
Светлая тема — `html[data-theme="light"]`, переключатель в шапке, выбор хранится в
`localStorage['xsisetvpn-theme']`. Язык — `localStorage['xsisetvpn-lang']`.
Серые полноширинные полосы не используются: глубина держится на карточках, рамках и отступах.
Поддержаны `prefers-reduced-motion`, `prefers-contrast: more`,
`prefers-reduced-transparency` и печать.

## Что проверено

- API (dry-панель): health, тарифы, валидация заказа (согласие, план, способ оплаты),
  демо-оплата и выдача ключа, `.txt` с `Content-Disposition`, чужой токен (403),
  ключ до оплаты (409), регистрация/дубликат/слабый пароль, вход/выход, список заказов,
  подпись Telegram (валидная/битая/старая).
- Браузер: анонимная покупка → демо-оплата → ключ → скачивание, восстановление заказа
  после перезагрузки, регистрация по почте, список ключей, отмена заказа, выход,
  переключение RU/EN (включая динамические блоки), тёмная и светлая темы.
- Lighthouse на `/` и `/privacy`: accessibility 100, best practices 100, SEO 100.
- Боевые ключи панели и провайдеров проверены read-only (`getMe`, список inbound'ов).
  Реальная выдача ключа и реальный счёт требуют контролируемого теста на проде.
