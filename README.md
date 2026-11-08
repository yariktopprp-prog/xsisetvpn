# xsiset vpn

Сайт VPN-сервиса: тёмная тема по умолчанию, светлая по кнопке, один синий акцент,
крупная типографика. Flask-бэкенд создаёт анонимные заказы, выставляет счёт в CryptoBot
или Platega, проверяет оплату и автоматически выдаёт VLESS-ключ через панель 3x-ui.
Пользователь получает ссылку-подписку на экране, файлом `.txt` и кнопкой копирования.

- Бот (пробный период): [@xsisetvpnbot](https://t.me/xsisetvpnbot)
- Поддержка: [@hkpde](https://t.me/hkpde)
- Серверы: Нидерланды (1), Швеция (2), Германия (1), обход белых списков (1) — всего 5
- Цены: 1 мес — 100 ₽, 3 мес — 270 ₽, 6 мес — 500 ₽, 12 мес — 900 ₽
- оплата на сайте: CryptoBot (USDT, TRX, TON) и Platega (карта, СБП);
- пробный период выдаётся **только в Telegram-боте**

## Что умеет

- покупка без регистрации: заказ получает одноразовый токен, ключ доступен только по нему;
- обязательное согласие с условиями и политикой (`consent_at`, `consent_version`);
- идемпотентная выдача ключа: один UUID и один `subId` на заказ;
- основной клиент создаётся на всех обычных inbound'ах, а для узла обхода белых
  списков — отдельный клиент с лимитом **20 ГБ на месяц** и тем же `subId`, поэтому
  обе группы серверов попадают в одну ссылку-подписку; выдача идёт по старой схеме:
  временный `subId` `_tmp` → `/root/untmp.sh` → общий `subId`; при сбое SSH —
  резервная одновременная выдача, при любом сбое удаляются оба клиента;
- фоновый сверщик оплат (`XSISET_RECONCILE_SECONDS`) и поллинг из браузера;
- ссылка-ключ и платёжные реквизиты хранятся только в зашифрованном виде (AES-256-GCM);
- автоочистка: выданные и неоплаченные заказы — через 24 часа, неудачные — через 2 часа.

## Структура

```
xsisetvpn/
├── index.html          страница: тарифы, оформление, оплата, ключ
├── privacy.html        политика конфиденциальности и условия использования
├── style.css           токены, темы, компоненты
├── script.js           RU/EN, тема, меню, заказ и оплата
├── theme-init.js       тема и класс js до первой отрисовки
├── 404.html
├── robots.txt
└── server/
    ├── app.py          Flask: статика, API, фоновая сверка оплат
    ├── config.py       тарифы, окружение, .env
    ├── db.py           SQLite: заказы, шифрование, миграция, очистка
    ├── secure.py       AES-256-GCM: мастер-ключ и ключ, производный от токена
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
$env:XSISET_RECONCILE_SECONDS = "0"
python app.py
```

Открыть <http://127.0.0.1:8124/>. Сайт и API отдаёт один процесс.

`XSISET_PANEL_MODE=dry` не трогает 3x-ui: ключ получает ссылку вида
`https://panel.example/sub/dry-...`. Реальные счета тоже не создаются, если не заданы
токены провайдеров.

## Как проходит покупка

1. Пользователь выбирает тариф, отмечает согласие и способ оплаты. Регистрации нет.
2. `POST /api/orders` создаёт заказ в SQLite (`pending`) и сразу создаёт счёт:
   - CryptoBot: `createInvoice` в рублях с `accepted_assets` (USDT/TRX/TON);
   - Platega: `POST /v2/transaction/process` (карта, СБП).
3. API возвращает заказ, `pay_url` и одноразовый `token`. Браузер опрашивает
   `GET /api/orders/<id>` каждые 4 секунды.
4. Сайт сам сверяет статус с провайдером. `paid/success/confirmed/completed` → заказ
   `paid`; `failed/canceled/expired/declined` → `failed`. Вебхуки не используются.
5. После `paid` сайт создаёт VLESS-клиента во всех inbound'ах, сохраняет зашифрованную
   ссылку-подписку и срок действия.
6. Пользователь получает `xsiset-vpn-<order_id>.txt` со ссылкой и инструкцией, может
   скопировать ключ или открыть подписку. Токен хранится в `localStorage` браузера.

Заказ живёт `XSISET_ORDER_TTL_HOURS` (по умолчанию 24 часа), затем становится `expired`.
Статусы: `pending` → `paid` | `failed` | `expired`. Выдача ключа идемпотентна.

## Приватность и шифрование

- Нет аккаунтов, почты, телефонов и профилей. Не сохраняются IP-адреса и журналы.
- Для rate-limit в памяти на минуты формируется необратимый хэш IP с солью; на диск он не пишется.
- Токен доступа хранится только как `SHA-256` (`th_...`). По базе его не восстановить.
- `key_sub_url`, `provider_id`, `pay_url` шифруются AES-256-GCM с уникальным nonce.
- Пока ключ выдан фоново и токен неизвестен, используется мастер-ключ (`v1:`).
  При первом обращении с корректным токеном запись перешифровывается ключом,
  производным от токена (`v2:`), и мастер-ключом больше не открывается.
- После миграции и очистки выполняется `VACUUM`, чтобы старые данные не остались
  в свободных страницах SQLite.
- Сторонние шрифты и аналитика не используются: CSP разрешает только свой домен.

## API

| Метод | Путь | Что делает |
|---|---|---|
| GET | `/api/health` | доступность платёжных провайдеров, валюта |
| GET | `/api/plans` | тарифы: месяцы, цена, цена за месяц, экономия |
| POST | `/api/orders` | `{plan_id, method, asset?, consent}` → заказ, `pay_url`, `token` |
| GET | `/api/orders/<id>?token=…` | статус, ссылка на оплату, ключ |
| POST | `/api/orders/<id>/cancel?token=…` | отменить ожидающий заказ |
| GET | `/api/orders/<id>/key.txt?token=…&lang=ru\|en` | файл с ключом |

Деньги в API — в копейках (`amount`), рядом лежит `price` в рублях.
Ошибки: `{"ok":false,"error":"code"}` с кодом 4xx/5xx.

## Настройки

Скопировать `server/.env.example` в `server/.env` и заполнить. Файл не коммитится
и наружу не отдаётся.

| Переменная | По умолчанию | Зачем |
|---|---|---|
| `XSISET_BOT` | `xsisetvpnbot` | имя бота без `@` |
| `XSISET_SUPPORT` | `hkpde` | поддержка в Telegram |
| `XSISET_CRYPTOPAY_TOKEN` | — | Crypto Pay API |
| `XSISET_CRYPTO_ASSETS` | `USDT,TRX,TON` | доступные монеты |
| `XSISET_PLATEGA_MERCHANT_ID` / `_SECRET` | — | Platega API |
| `XSISET_PANEL_URL` / `_TOKEN` | — | 3x-ui, URL панели и Bearer-токен |
| `XSISET_PANEL_INBOUNDS` | `5,11,13,16,17` | inbound'ы для клиента |
| `XSISET_PANEL_SUB_BASE` | — | база ссылки-подписки (`/sub` добавится сам) |
| `XSISET_PANEL_DOMAIN` / `_SUB_PORT` | `xsisetsweden3x-ui1.site` / `2096` | если `SUB_BASE` пуст |
| `XSISET_PANEL_MODE` | `live` | `dry` — не писать в панель |
| `XSISET_PANEL_VERIFY_TLS` | `true` | проверка TLS панели |
| `XSISET_PANEL_SSH_HOST` / `_PORT` / `_USER` / `_PASSWORD` | — | старая схема: запуск `/root/untmp.sh` по SSH |
| `XSISET_PANEL_UNTMP_CMD` | `/root/untmp.sh` | команда, убирающая `_tmp` у обхода |
| `XSISET_SECRET_KEY` | генерируется | мастер-ключ шифрования; смена ломает старые ключи |
| `XSISET_TRUST_PROXY` | `0` | доверять `X-Forwarded-For` только за своим прокси |
| `XSISET_RECONCILE_SECONDS` | `120` | период фоновой сверки и очистки, `0` — выключить |
| `XSISET_ORDER_TTL_HOURS` | `24` | срок жизни заказа |
| `XSISET_PAYMENT_TTL_MINUTES` | `60` | срок жизни счёта |
| `XSISET_CONSENT_VERSION` | `2026-11-05` | версия согласия |
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

> Для нескольких gunicorn-воркеров фоновая сверка запустится в каждом процессе.
> Если это нежелательно, оставьте `-w 1` или вынесите сверку в отдельный сервис.

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

    location = /privacy { proxy_pass http://127.0.0.1:8124; }
    location = /privacy.html { proxy_pass http://127.0.0.1:8124; }
    location = /terms { proxy_pass http://127.0.0.1:8124; }
    location = /terms.html { proxy_pass http://127.0.0.1:8124; }

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

`certbot --nginx -d vpn.example.com`. HTTPS обязателен. При работе за nginx включите
`XSISET_TRUST_PROXY=1`, чтобы корректно считать rate-limit по реальному IP.

CSP и остальные заголовки ставит Flask (`app.py`), в nginx их дублировать не нужно.
Inline-скриптов нет: тема вынесена в `theme-init.js`, поэтому `script-src 'self'`
работает без хешей и `unsafe-inline`.

### Бэкап

```bash
sudo -u www-data sqlite3 /opt/xsisetvpn/server/data/orders.sqlite3 \
  ".backup '/var/backups/xsisetvpn-$(date +%F).sqlite3'"
```

В базе только технические заказы; ключи и платёжные реквизиты зашифрованы.
Ссылки-подписки остаются рабочими в панели 3x-ui даже при потере базы.

## Безопасность

- Токен доступа — 32 hex, хранится только как `SHA-256`; сравнение — `hmac.compare_digest`.
- Чувствительные поля — AES-256-GCM; nonce уникален для каждой записи.
- `POST /api/orders` — 30 заказов с IP за 10 минут; опрос — 90 запросов в минуту;
  скачивание ключа — 15 запросов в минуту.
- ID заказа и токен — случайные (`secrets`), перебор не имеет смысла.
- `server/`, `.env`, база и скрытые файлы наружу не отдаются: статика только по белому списку.
- Проверка `Origin` для всех POST/PUT/PATCH/DELETE.
- CSP без `unsafe-inline` для скриптов, `nosniff`, `Referrer-Policy: no-referrer`,
  `X-Frame-Options: DENY`, `Permissions-Policy`.
- Сайт не принимает и не хранит карточные данные: только идентификатор счёта у провайдера.
- Согласие фиксируется датой и версией документа; IP не сохраняется.

## Дизайн

Общие токены: `--bg #000`, карточки `#161618`, чипы `#2e2e30`, синий `#0071e3`.
Светлая тема — `html[data-theme="light"]`, переключатель в шапке, выбор хранится в
`localStorage['xsisetvpn-theme']`. Язык — `localStorage['xsisetvpn-lang']`.
Поддержаны `prefers-reduced-motion`, `prefers-contrast: more`,
`prefers-reduced-transparency` и печать.

## Что проверено

- API (dry-панель): health, тарифы, валидация заказа, согласие, cross-origin, чужой токен (403),
  ключ до оплаты (409), отмена, `.txt` на RU/EN с человеческой датой, `Content-Disposition`.
- Шифрование: `v1`/`v2`, апгрейд при первом доступе, отсутствие открытых ключей и платёжных
  ID в файле БД, миграция старой схемы, `VACUUM` после очистки.
- Панель 3x-ui: клиент реально создаётся во всех 5 inbound'ах с одним `subId` по старой
  схеме `_tmp` → `/root/untmp.sh`, затем удаляется через `/panel/api/clients/del/{email}`;
  сетевые/HTTP/JSON-ошибки → `PanelError`, без 500 у пользователя.
- Браузер: покупка, ключ, скачивание, смена языка (включая `lang` в ссылке и статусы),
  поддержка `@hkpde`, тёмная и светлая темы.
- Lighthouse на `/`: accessibility 100, best practices 100, SEO 100, ошибок в консоли нет.
