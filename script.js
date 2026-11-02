/* =========================================================
   xsiset vpn: язык, тема, меню, появление блоков, аккаунт,
   заказ и оплата на сайте.
   Сайт сам создаёт заказ, выставляет счёт (CryptoBot/Platega),
   проверяет оплату и после неё отдаёт .txt с ключом.
   ========================================================= */

(function () {
  'use strict';

  const I18N = {
    ru: {
      'meta.title': 'xsiset vpn · VPN без границ',
      'meta.desc': 'xsiset vpn: пять серверов в Европе, обход белых списков, оплата картой и криптой на сайте, ключ файлом .txt сразу после оплаты.',
      'a11y.skip': 'К содержимому',
      brand: 'xsiset',

      'aria.lang': 'Язык',
      'aria.theme': 'Сменить тему',
      'aria.menu': 'Меню',
      'aria.term': 'Список серверов xsiset vpn',
      'aria.top': 'Наверх',

      'nav.servers': 'Серверы',
      'nav.features': 'Возможности',
      'nav.pricing': 'Тарифы',
      'nav.account': 'Мои ключи',
      'nav.faq': 'Вопросы',
      'nav.cta': 'Подключиться',

      'hero.live': '5 серверов онлайн',
      'hero.badge': 'обход белых списков',
      'hero.t1': 'Интернет',
      'hero.t2': 'без границ.',
      'hero.text': 'Пять серверов в Европе. Оплата на сайте, ключ — файлом .txt.',
      'hero.cta1': 'Выбрать тариф',
      'hero.cta2': 'Открыть бота',
      'term.state': '5 серверов',

      'servers.title': 'Серверы в Европе',
      'servers.text': 'Один тариф открывает все узлы. Отдельный сервер — для обхода белых списков.',
      'servers.nl': 'Нидерланды',
      'servers.nl.d': 'Выход в интернет через Нидерланды.',
      'servers.se': 'Швеция',
      'servers.se.d': 'Два отдельных сервера в Швеции.',
      'servers.de': 'Германия',
      'servers.de.d': 'Выход в интернет через Германию.',
      'servers.wl': 'Обход белых списков',
      'servers.wl.d': 'Для случаев, когда обычный VPN не проходит по белым спискам.',
      'servers.one': '1 сервер',
      'servers.two': '2 сервера',
      'node.online': 'доступен',

      'feat.title': 'Всё на сайте',
      'feat.text': 'Выбор тарифа, оплата, выдача ключа и поддержка — без посредников.',
      'feat.pay.t': 'Карта и крипта',
      'feat.pay.d': 'CryptoBot: USDT, TRX, TON. Platega: карта и СБП. Счёт создаётся на сайте.',
      'feat.auto.t': 'Ключ сразу',
      'feat.auto.d': 'После оплаты сайт сам создаёт доступ на всех пяти серверах.',
      'feat.renew.t': 'Файл с ключом',
      'feat.renew.d': 'Ключ скачивается как .txt: ссылка-подписка и инструкция внутри.',
      'feat.help.t': 'Поддержка',
      'feat.help.d': 'Вопросы по подключению — в @xsisetvpnbot.',

      'how.title': 'Три шага',
      'how.text': 'От выбора тарифа до рабочего ключа — пара минут.',
      'how.s1.t': 'Выберите тариф',
      'how.s1.d': '1, 3, 6 или 12 месяцев. Все пять серверов включены.',
      'how.s2.t': 'Оплатите на сайте',
      'how.s2.d': 'CryptoBot или Platega: карта, СБП, USDT, TRX, TON.',
      'how.s3.t': 'Скачайте ключ',
      'how.s3.d': 'Файл .txt со ссылкой-подпиской и инструкцией по подключению.',

      'price.title': 'Тарифы',
      'price.text': 'Один тариф — все пять серверов. Оплата в рублях, ключ файлом .txt.',
      'price.trial': 'Пробный период выдаётся только в Telegram-боте',
      'plan.m1': '1 месяц',
      'plan.m1.per': '100 ₽ в месяц',
      'plan.m1.note': 'Оплата раз в месяц',
      'plan.m3': '3 месяца',
      'plan.m3.per': '90 ₽ в месяц',
      'plan.m3.note': 'Экономия 30 ₽',
      'plan.m6': '6 месяцев',
      'plan.m6.per': '83 ₽ в месяц',
      'plan.m6.note': 'Экономия 100 ₽',
      'plan.m12': '12 месяцев',
      'plan.m12.note': '75 ₽ в месяц · экономия 300 ₽',
      'plan.best': 'выгодно',
      'plan.all': 'Все 5 серверов',
      'plan.wl': 'Обход белых списков',
      'plan.key': 'Ключ файлом .txt',
      'plan.cta': 'Оплатить',

      'co.label': 'Заказ',
      'co.formTitle': 'Оформление',
      'co.cancel': 'Выбрать другой тариф',
      'co.who': 'Кто покупает',
      'co.mode.anon': 'Без аккаунта',
      'co.mode.email': 'Почта',
      'co.mode.tg': 'Telegram',
      'co.anonNote': 'Аккаунт не нужен. После оплаты ключ сразу скачается файлом — сохраните его.',
      'co.email': 'Почта',
      'co.password': 'Пароль',
      'co.login': 'Войти',
      'co.register': 'Создать аккаунт',
      'co.signedAs': 'Вы вошли как',
      'co.logout': 'Выйти',
      'co.tgNote': 'Вход через Telegram привязывает ключи к аккаунту. Виджет работает только на домене с HTTPS.',
      'co.tgSigned': 'Вы вошли через Telegram. Ключи будут привязаны к аккаунту.',
      'co.tgAccountNote': 'Вы уже вошли в аккаунт. Ключи привязаны к нему.',
      'co.tgUnavailable': 'Вход через Telegram временно недоступен. Купите без аккаунта или войдите по почте.',
      'co.tgConsentNeeded': 'Отметьте согласие, чтобы войти через Telegram.',
      'co.method': 'Способ оплаты',
      'co.cryptoSub': 'USDT, TRX, TON',
      'co.plategaSub': 'Карта, СБП',
      'co.asset': 'Монета',
      'co.consent1': 'Мне 18 лет и больше.',
      'co.consent2': 'Я согласен с',
      'co.consentLink': 'политикой обработки персональных данных',
      'co.consent3': 'и принимаю условия сервиса.',
      'co.payNow': 'Оплатить',
      'co.creating': 'Создаём заказ и счёт…',
      'co.busy': 'Подождите, создаём заказ…',
      'co.signInFirst': 'Войдите по почте или выберите «Без аккаунта».',
      'co.tgSignInFirst': 'Войдите через Telegram или выберите «Без аккаунта».',
      'co.consentNeeded': 'Отметьте согласие на обработку персональных данных.',
      'co.pleaseWait': 'Секунду…',
      'co.authOk': 'Готово. Аккаунт активен.',
      'co.authFail': 'Не удалось войти. Попробуйте ещё раз.',
      'co.emailBad': 'Проверьте адрес почты.',
      'co.passwordWeak': 'Пароль должен быть не короче 8 символов.',
      'co.emailTaken': 'Аккаунт с такой почтой уже есть. Войдите.',
      'co.badCreds': 'Неверная почта или пароль.',
      'co.tooMany': 'Слишком много попыток. Попробуйте позже.',
      'co.payUnavailable': 'Этот способ оплаты временно недоступен.',
      'co.invoiceFailed': 'Платёжный сервис не ответил. Попробуйте другой способ оплаты.',
      'co.error': 'Что-то пошло не так. Попробуйте ещё раз.',
      'co.offline': 'Сервер заказов недоступен. Попробуйте ещё раз через минуту.',
      'co.notFound': 'Заказ не найден. Создайте новый.',

      'co.payLabel': 'Оплата',
      'co.awaiting': 'Ожидает оплаты',
      'co.pending': 'Ожидает оплаты',
      'co.paid': 'Оплачено',
      'co.failed': 'Ошибка оплаты',
      'co.expired': 'Истёк',
      'co.number': 'Номер',
      'co.plan': 'Тариф',
      'co.sum': 'Сумма',
      'co.validUntil': 'Действует до',
      'co.payHint': 'Откройте оплату и завершите платёж. Статус обновится сам — страницу можно не закрывать.',
      'co.issuing': 'Оплата получена. Выпускаем ключ — это займёт несколько секунд.',
      'co.openPay': 'Перейти к оплате',
      'co.check': 'Проверить оплату',
      'co.demo': 'Демо-оплата',
      'co.cancelPay': 'Отменить заказ',
      'co.checking': 'Проверяем статус…',
      'co.stillPending': 'Оплата пока не поступила. Проверьте ещё раз через минуту.',
      'co.closedHint': 'Заказ больше не ждёт оплату. Создайте новый — это займёт пару секунд.',
      'co.closedStatus': 'Заказ закрыт. Создайте новый.',
      'co.cancelled': 'Заказ отменён.',
      'co.cancelFailed': 'Не удалось отменить заказ. Обновите страницу.',

      'co.doneLabel': 'Ключ',
      'co.doneTitle': 'Ключ готов',
      'co.doneHint': 'Ключ — это ссылка-подписка. Скачайте файл: внутри ссылка и инструкция по подключению. Ссылку можно скопировать и вставить в приложение вручную.',
      'co.download': 'Скачать ключ (.txt)',
      'co.copy': 'Скопировать ключ',
      'co.copied': 'Ключ скопирован.',
      'co.copyFailed': 'Не удалось скопировать. Выделите ссылку вручную.',
      'co.newOrder': 'Новый заказ',
      'co.saved': 'Ключ сохранён на этом устройстве. Скачайте файл — он понадобится для подключения.',

      'acc.title': 'Мои ключи',
      'acc.text': 'Войдите по почте или через Telegram — купленные ключи будут под рукой. Аккаунт не обязателен.',
      'acc.guestTitle': 'Покупка без аккаунта',
      'acc.guestText': 'Ключ выдаётся сразу после оплаты и скачивается файлом. Вход нужен только чтобы хранить ключи на сайте.',
      'acc.pick': 'Выбрать тариф',
      'acc.empty': 'Оплаченных заказов пока нет.',
      'acc.loading': 'Загружаем ключи…',
      'acc.logout': 'Выйти',
      'acc.authOk': 'Вход выполнен. Ключи ниже.',
      'acc.authFail': 'Не удалось войти через Telegram. Попробуйте ещё раз.',
      'acc.tgAccount': 'Аккаунт Telegram',
      'acc.pending': 'Ждёт оплаты',
      'acc.continue': 'Продолжить оплату',
      'acc.validUntil': 'до',
      'acc.download': 'Скачать .txt',
      'acc.copy': 'Скопировать',

      'faq.title': 'Вопросы',
      'faq.text': 'Коротко о том, как всё устроено.',
      'faq.q1': 'Как проходит оплата?',
      'faq.a1': 'Выбираете тариф и способ оплаты. Сайт создаёт счёт в CryptoBot или Platega, сам проверяет оплату и сразу выдаёт ключ. Никуда переходить за ключом не нужно.',
      'faq.q2': 'Какие способы оплаты есть?',
      'faq.a2': 'CryptoBot принимает USDT, TRX и TON. Platega — банковскую карту и СБП. Все платежи в рублях, комиссию провайдер показывает до подтверждения.',
      'faq.q3': 'Можно купить без аккаунта?',
      'faq.a3': 'Да. Режим «Без аккаунта» выдаёт ключ сразу после оплаты — сохраните скачанный файл. Если хотите хранить ключи на сайте, войдите по почте или через Telegram.',
      'faq.q4': 'Есть пробный период?',
      'faq.a4': 'Пробный доступ выдаётся только в Telegram-боте @xsisetvpnbot. На сайте пробного периода нет — здесь можно сразу купить полный тариф.',
      'faq.q5': 'Что такое обход белых списков?',
      'faq.a5': 'Это отдельный сервер для случаев, когда обычные VPN-подключения не проходят из-за ограничений по белым спискам. Он входит в любой тариф.',
      'faq.q6': 'Что внутри файла с ключом?',
      'faq.a6': 'Ссылка-подписка и короткая инструкция. Скопируйте ссылку в Happ, Streisand, v2rayNG или FoXray, обновите подписку и включите VPN.',

      'cta.title': 'Подключиться',
      'cta.text': 'Выберите тариф и оплатите на сайте. Если что-то пошло не так, напишите нам.',
      'cta.bot': 'Открыть @xsisetvpnbot',
      'ftr.mail': 'Почта',
      'ftr.privacy': 'Политика ПД'
    },

    en: {
      'meta.title': 'xsiset vpn · VPN without borders',
      'meta.desc': 'xsiset vpn: five servers in Europe, whitelist bypass, card and crypto payment on the site, key as a .txt file right after payment.',
      'a11y.skip': 'Skip to content',
      brand: 'xsiset',

      'aria.lang': 'Language',
      'aria.theme': 'Toggle theme',
      'aria.menu': 'Menu',
      'aria.term': 'xsiset vpn server list',
      'aria.top': 'Back to top',

      'nav.servers': 'Servers',
      'nav.features': 'Features',
      'nav.pricing': 'Pricing',
      'nav.account': 'My keys',
      'nav.faq': 'FAQ',
      'nav.cta': 'Get started',

      'hero.live': '5 servers online',
      'hero.badge': 'whitelist bypass',
      'hero.t1': 'The internet',
      'hero.t2': 'without borders.',
      'hero.text': 'Five servers in Europe. Pay on the site, get the key as a .txt file.',
      'hero.cta1': 'Choose a plan',
      'hero.cta2': 'Open the bot',
      'term.state': '5 servers',

      'servers.title': 'Servers in Europe',
      'servers.text': 'One plan opens every node. A separate server handles whitelist bypass.',
      'servers.nl': 'Netherlands',
      'servers.nl.d': 'Internet access through the Netherlands.',
      'servers.se': 'Sweden',
      'servers.se.d': 'Two separate servers in Sweden.',
      'servers.de': 'Germany',
      'servers.de.d': 'Internet access through Germany.',
      'servers.wl': 'Whitelist bypass',
      'servers.wl.d': 'For cases when a regular VPN is blocked by whitelist rules.',
      'servers.one': '1 server',
      'servers.two': '2 servers',
      'node.online': 'available',

      'feat.title': 'All on the site',
      'feat.text': 'Pick a plan, pay, get the key and support — no middleman.',
      'feat.pay.t': 'Card and crypto',
      'feat.pay.d': 'CryptoBot: USDT, TRX, TON. Platega: card and SBP. The invoice is created here.',
      'feat.auto.t': 'Key right away',
      'feat.auto.d': 'After payment the site provisions access on all five servers.',
      'feat.renew.t': 'Key as a file',
      'feat.renew.d': 'Download a .txt with the subscription link and setup steps.',
      'feat.help.t': 'Support',
      'feat.help.d': 'Setup questions — in @xsisetvpnbot.',

      'how.title': 'Three steps',
      'how.text': 'From picking a plan to a working key — a couple of minutes.',
      'how.s1.t': 'Choose a plan',
      'how.s1.d': '1, 3, 6 or 12 months. All five servers included.',
      'how.s2.t': 'Pay on the site',
      'how.s2.d': 'CryptoBot or Platega: card, SBP, USDT, TRX, TON.',
      'how.s3.t': 'Download the key',
      'how.s3.d': 'A .txt with the subscription link and setup instructions.',

      'price.title': 'Pricing',
      'price.text': 'One plan covers all five servers. Paid in rubles, key as a .txt file.',
      'price.trial': 'Trial access is available only in the Telegram bot',
      'plan.m1': '1 month',
      'plan.m1.per': '100 ₽ per month',
      'plan.m1.note': 'Billed monthly',
      'plan.m3': '3 months',
      'plan.m3.per': '90 ₽ per month',
      'plan.m3.note': 'Save 30 ₽',
      'plan.m6': '6 months',
      'plan.m6.per': '83 ₽ per month',
      'plan.m6.note': 'Save 100 ₽',
      'plan.m12': '12 months',
      'plan.m12.note': '75 ₽ per month · save 300 ₽',
      'plan.best': 'best value',
      'plan.all': 'All 5 servers',
      'plan.wl': 'Whitelist bypass',
      'plan.key': 'Key as a .txt file',
      'plan.cta': 'Pay',

      'co.label': 'Order',
      'co.formTitle': 'Checkout',
      'co.cancel': 'Choose another plan',
      'co.who': 'Who is buying',
      'co.mode.anon': 'No account',
      'co.mode.email': 'Email',
      'co.mode.tg': 'Telegram',
      'co.anonNote': 'No account needed. After payment the key downloads as a file — keep it safe.',
      'co.email': 'Email',
      'co.password': 'Password',
      'co.login': 'Sign in',
      'co.register': 'Create account',
      'co.signedAs': 'Signed in as',
      'co.logout': 'Sign out',
      'co.tgNote': 'Signing in with Telegram links keys to your account. The widget works only on an HTTPS domain.',
      'co.tgSigned': 'You are signed in with Telegram. Keys will be linked to this account.',
      'co.tgAccountNote': 'You are already signed in. Keys are linked to this account.',
      'co.tgUnavailable': 'Telegram sign-in is temporarily unavailable. Buy without an account or use email.',
      'co.tgConsentNeeded': 'Tick the consent box to sign in with Telegram.',
      'co.method': 'Payment method',
      'co.cryptoSub': 'USDT, TRX, TON',
      'co.plategaSub': 'Card, SBP',
      'co.asset': 'Coin',
      'co.consent1': 'I am 18 or older.',
      'co.consent2': 'I agree to the',
      'co.consentLink': 'personal data processing policy',
      'co.consent3': 'and accept the terms of service.',
      'co.payNow': 'Pay',
      'co.creating': 'Creating the order and invoice…',
      'co.busy': 'One moment, creating the order…',
      'co.signInFirst': 'Sign in with email or choose “No account”.',
      'co.tgSignInFirst': 'Sign in with Telegram or choose “No account”.',
      'co.consentNeeded': 'Please accept the personal data processing policy.',
      'co.pleaseWait': 'One moment…',
      'co.authOk': 'Done. Your account is active.',
      'co.authFail': 'Sign-in failed. Please try again.',
      'co.emailBad': 'Check the email address.',
      'co.passwordWeak': 'The password must be at least 8 characters.',
      'co.emailTaken': 'An account with this email already exists. Please sign in.',
      'co.badCreds': 'Wrong email or password.',
      'co.tooMany': 'Too many attempts. Please try later.',
      'co.payUnavailable': 'This payment method is temporarily unavailable.',
      'co.invoiceFailed': 'The payment service did not respond. Try another method.',
      'co.error': 'Something went wrong. Please try again.',
      'co.offline': 'The order service is unavailable. Please try again in a minute.',
      'co.notFound': 'Order not found. Please create a new one.',

      'co.payLabel': 'Payment',
      'co.awaiting': 'Awaiting payment',
      'co.pending': 'Awaiting payment',
      'co.paid': 'Paid',
      'co.failed': 'Payment failed',
      'co.expired': 'Expired',
      'co.number': 'Order',
      'co.plan': 'Plan',
      'co.sum': 'Total',
      'co.validUntil': 'Valid until',
      'co.payHint': 'Open the payment page and finish the payment. The status updates automatically — you can keep this page open.',
      'co.issuing': 'Payment received. Issuing the key — a few seconds.',
      'co.openPay': 'Go to payment',
      'co.check': 'Check payment',
      'co.demo': 'Demo payment',
      'co.cancelPay': 'Cancel order',
      'co.checking': 'Checking the status…',
      'co.stillPending': 'Payment has not arrived yet. Check again in a minute.',
      'co.closedHint': 'This order is no longer awaiting payment. Create a new one in a couple of seconds.',
      'co.closedStatus': 'Order closed. Please create a new one.',
      'co.cancelled': 'Order cancelled.',
      'co.cancelFailed': 'Could not cancel the order. Please reload the page.',

      'co.doneLabel': 'Key',
      'co.doneTitle': 'Key is ready',
      'co.doneHint': 'The key is the subscription link. Download the file: it contains the link and setup steps. You can also copy the link into your app manually.',
      'co.download': 'Download key (.txt)',
      'co.copy': 'Copy key',
      'co.copied': 'Key copied.',
      'co.copyFailed': 'Could not copy. Please select the link manually.',
      'co.newOrder': 'New order',
      'co.saved': 'The key is saved on this device. Download the file — you will need it to connect.',

      'acc.title': 'My keys',
      'acc.text': 'Sign in with email or Telegram and keep your keys in one place. An account is optional.',
      'acc.guestTitle': 'Buy without an account',
      'acc.guestText': 'The key is issued right after payment and downloads as a file. Sign-in is only needed to store keys on the site.',
      'acc.pick': 'Choose a plan',
      'acc.empty': 'No paid orders yet.',
      'acc.loading': 'Loading keys…',
      'acc.logout': 'Sign out',
      'acc.authOk': 'Signed in. Your keys are below.',
      'acc.authFail': 'Telegram sign-in failed. Please try again.',
      'acc.tgAccount': 'Telegram account',
      'acc.pending': 'Awaiting payment',
      'acc.continue': 'Continue payment',
      'acc.validUntil': 'until',
      'acc.download': 'Download .txt',
      'acc.copy': 'Copy',

      'faq.title': 'Questions',
      'faq.text': 'The short version of how it works.',
      'faq.q1': 'How does payment work?',
      'faq.a1': 'Pick a plan and a payment method. The site creates an invoice in CryptoBot or Platega, verifies the payment itself and issues the key right away. No need to go anywhere else.',
      'faq.q2': 'Which payment methods are available?',
      'faq.a2': 'CryptoBot accepts USDT, TRX and TON. Platega accepts bank cards and SBP. Everything is charged in rubles; the provider shows its fee before you confirm.',
      'faq.q3': 'Can I buy without an account?',
      'faq.a3': 'Yes. “No account” mode issues the key right after payment — keep the downloaded file. If you want your keys stored on the site, sign in with email or Telegram.',
      'faq.q4': 'Is there a free trial?',
      'faq.a4': 'Trial access is available only in the @xsisetvpnbot Telegram bot. The site has no trial — here you buy a full plan right away.',
      'faq.q5': 'What is whitelist bypass?',
      'faq.a5': 'A separate server for cases when regular VPN connections are blocked by whitelist restrictions. It is included in every plan.',
      'faq.q6': 'What is inside the key file?',
      'faq.a6': 'The subscription link and brief instructions. Paste the link into Happ, Streisand, v2rayNG or FoXray, update the subscription and turn the VPN on.',

      'cta.title': 'Get connected',
      'cta.text': 'Choose a plan and pay on the site. If something goes wrong, message us.',
      'cta.bot': 'Open @xsisetvpnbot',
      'ftr.mail': 'Email',
      'ftr.privacy': 'Privacy policy'
    }
  };

  const THEME_KEY = 'xsisetvpn-theme';
  const LANG_KEY = 'xsisetvpn-lang';
  const ORDER_KEY = 'xsisetvpn-order';
  const root = document.documentElement;
  const nodes = document.querySelectorAll('[data-i18n]');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function dict() {
    return I18N[root.lang] || I18N.ru;
  }

  function t(key) {
    return dict()[key] || I18N.ru[key] || '';
  }

  function langCode() {
    return root.lang === 'en' ? 'en' : 'ru';
  }

  function $(id) {
    return document.getElementById(id);
  }

  /* ---------------------- ЯЗЫК ---------------------- */

  const langButtons = document.querySelectorAll('.lang__btn');

  function applyLang(lang) {
    const code = lang === 'en' ? 'en' : 'ru';
    const d = I18N[code];

    root.lang = code;

    nodes.forEach(function (el) {
      const key = el.getAttribute('data-i18n');
      if (d[key]) el.textContent = d[key];
    });

    document.querySelectorAll('[data-i18n-aria]').forEach(function (el) {
      const key = el.getAttribute('data-i18n-aria');
      if (d[key]) el.setAttribute('aria-label', d[key]);
    });

    langButtons.forEach(function (b) {
      const active = b.getAttribute('data-lang') === code;
      b.classList.toggle('is-active', active);
      b.setAttribute('aria-pressed', active ? 'true' : 'false');
    });

    if (d['meta.title']) document.title = d['meta.title'];
    const desc = document.querySelector('meta[name="description"]');
    if (desc && d['meta.desc']) desc.setAttribute('content', d['meta.desc']);

    try { localStorage.setItem(LANG_KEY, code); } catch (e) { /* не критично */ }

    renderDynamic();
  }

  langButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      applyLang(btn.dataset.lang);
    });
  });

  /* ---------------------- ТЕМА ---------------------- */

  const themeBtn = $('themeBtn');
  const themeMeta = document.querySelector('meta[name="theme-color"]');

  function setTheme(theme, persist) {
    if (theme === 'light') {
      root.setAttribute('data-theme', 'light');
    } else {
      root.removeAttribute('data-theme');
    }
    if (themeMeta) themeMeta.setAttribute('content', theme === 'light' ? '#ffffff' : '#000000');
    if (persist) {
      try { localStorage.setItem(THEME_KEY, theme); } catch (e) { /* не критично */ }
    }
  }

  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      setTheme(root.getAttribute('data-theme') === 'light' ? 'dark' : 'light', true);
    });
  }

  setTheme(root.getAttribute('data-theme') === 'light' ? 'light' : 'dark', false);

  /* ---------------------- ПРОКРУТКА ШАПКИ ---------------------- */

  const hdr = $('hdr');
  let hdrTicking = false;

  function onScroll() {
    if (hdrTicking) return;
    hdrTicking = true;
    requestAnimationFrame(function () {
      if (hdr) hdr.classList.toggle('is-scrolled', window.scrollY > 6);
      hdrTicking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------------------- МЕНЮ ---------------------- */

  const burger = $('burger');
  const nav = $('nav');

  function closeMenu(returnFocus) {
    if (!nav || !burger) return;
    nav.classList.remove('is-open');
    burger.classList.remove('is-open');
    burger.setAttribute('aria-expanded', 'false');
    if (returnFocus) burger.focus();
  }

  if (burger && nav) {
    burger.addEventListener('click', function () {
      const open = !nav.classList.contains('is-open');
      nav.classList.toggle('is-open', open);
      burger.classList.toggle('is-open', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    nav.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () { closeMenu(false); });
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) closeMenu(true);
    });

    window.addEventListener('resize', function () {
      if (window.innerWidth > 734 && nav.classList.contains('is-open')) closeMenu(false);
    });
  }

  /* ---------------------- ПОЯВЛЕНИЕ БЛОКОВ ---------------------- */

  const reveals = document.querySelectorAll('.reveal');

  function showReveal(el) {
    el.classList.add('is-in');
    setTimeout(function () { el.classList.add('is-settled'); }, 900);
  }

  if (reduceMotion || !('IntersectionObserver' in window)) {
    reveals.forEach(showReveal);
  } else {
    let ioStarted = false;
    const io = new IntersectionObserver(function (entries) {
      ioStarted = true;
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          showReveal(entry.target);
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

    reveals.forEach(function (el) { io.observe(el); });

    setTimeout(function () {
      if (ioStarted) return;
      io.disconnect();
      reveals.forEach(showReveal);
    }, 2000);
  }

  /* ---------------------- ПАРАЛЛАКС ---------------------- */

  const heroVisual = document.querySelector('.hero__visual');

  if (heroVisual && !reduceMotion) {
    let target = 0;
    let current = 0;
    let frame = null;

    function followScroll() {
      target = Math.min(window.scrollY, 900);
      current += (target - current) * 0.09;
      heroVisual.style.transform = 'translate3d(0,' + (current * 0.05).toFixed(2) + 'px,0)';

      if (Math.abs(target - current) > 0.1) {
        frame = requestAnimationFrame(followScroll);
      } else {
        frame = null;
      }
    }

    function requestFrame() {
      if (!frame) frame = requestAnimationFrame(followScroll);
    }

    window.addEventListener('scroll', requestFrame, { passive: true });
    requestFrame();
  }

  /* ---------------------- ЭЛЕМЕНТЫ ---------------------- */

  const el = {
    plans: document.querySelectorAll('.plan__btn[data-plan]'),
    checkout: $('checkout'),
    payment: $('paymentPanel'),
    done: $('donePanel'),
    checkoutStatus: $('checkoutStatus'),
    cancelPlan: $('cancelBtn'),
    orderPlan: $('orderPlan'),
    orderAmount: $('orderAmount'),
    startPay: $('startPayBtn'),
    startPaySum: $('startPaySum'),
    consent: $('consentBox'),
    segs: document.querySelectorAll('.seg__btn[data-mode]'),
    panes: document.querySelectorAll('.co-pane[data-pane]'),
    authGuest: $('authGuest'),
    authUser: $('authUser'),
    authWho: $('authWho'),
    authEmail: $('authEmail'),
    authPassword: $('authPassword'),
    login: $('loginBtn'),
    register: $('registerBtn'),
    logout: $('logoutBtn'),
    authStatus: $('authStatus'),
    tgWidget: $('tgWidget'),
    tgNote: $('tgNote'),
    tgConsent: $('tgConsent'),
    tgStatus: $('tgStatus'),
    payRadios: document.querySelectorAll('input[name="payMethod"]'),
    payLabels: document.querySelectorAll('.pay'),
    assetField: $('assetField'),
    asset: $('payAsset'),
    orderStatus: $('orderStatus'),
    payOrderId: $('payOrderId'),
    payPlan: $('payPlan'),
    payAmount: $('payAmount'),
    payHint: $('payHint'),
    openPay: $('openPayBtn'),
    check: $('checkBtn'),
    demo: $('demoBtn'),
    cancelPay: $('cancelPayBtn'),
    payStatus: $('payStatus'),
    doneId: $('doneId'),
    donePlan: $('donePlan'),
    doneValid: $('doneValid'),
    doneKey: $('doneKey'),
    download: $('downloadBtn'),
    copyKey: $('copyKeyBtn'),
    newOrder: $('newOrderBtn'),
    doneStatus: $('doneStatus'),
    accGuest: $('accGuest'),
    accUser: $('accUser'),
    accName: $('accName'),
    accMeta: $('accMeta'),
    accLogout: $('accLogout'),
    accList: $('accList'),
    accEmpty: $('accEmpty'),
    accStatus: $('accStatus')
  };

  /* ---------------------- ДАННЫЕ ---------------------- */

  const state = {
    planId: null,
    planPrice: 0,
    mode: 'anon',
    method: 'cryptobot',
    asset: 'USDT',
    user: null,
    orders: [],
    order: null,
    token: '',
    timer: null,
    busy: false,
    demo: false,
    health: null,
    tgInjected: false
  };

  const PRICE = { m1: 100, m3: 270, m6: 500, m12: 900 };

  function money(value) {
    const locale = langCode() === 'en' ? 'en-US' : 'ru-RU';
    return new Intl.NumberFormat(locale).format(value) + ' ₽';
  }

  function fmtDate(iso) {
    if (!iso) return '—';
    const date = new Date(iso);
    if (isNaN(date.getTime())) return '—';
    return date.toLocaleDateString(langCode() === 'en' ? 'en-GB' : 'ru-RU', {
      day: '2-digit', month: '2-digit', year: 'numeric'
    });
  }

  function planTitle(planId) {
    return t('plan.' + planId) || planId;
  }

  function displayName(user) {
    if (!user) return '';
    if (user.name) return user.name;
    if (user.email) return user.email;
    if (user.telegram_username) return '@' + user.telegram_username;
    return t('acc.tgAccount');
  }

  function setStatus(node, text, kind) {
    if (!node) return;
    node.textContent = text || '';
    node.classList.toggle('is-error', kind === 'error');
    node.classList.toggle('is-ok', kind === 'ok');
  }

  function tokenQuery() {
    return state.token ? '?token=' + encodeURIComponent(state.token) : '';
  }

  async function api(path, options) {
    const opts = Object.assign({ headers: { Accept: 'application/json' }, cache: 'no-store' }, options || {});
    if (opts.body && typeof opts.body !== 'string') {
      opts.headers = Object.assign({}, opts.headers, { 'Content-Type': 'application/json' });
      opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(path, opts);
    let data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    if (!res.ok) {
      const error = new Error((data && data.error) || 'http_' + res.status);
      error.status = res.status;
      error.code = (data && data.error) || '';
      throw error;
    }
    return data || {};
  }

  /* ---------------------- АККАУНТ ---------------------- */

  function renderAuth() {
    const user = state.user;
    const tgReady = Boolean(state.health && state.health.telegram_login);

    if (el.authGuest) el.authGuest.hidden = Boolean(user);
    if (el.authUser) el.authUser.hidden = !user;
    if (el.authWho) el.authWho.textContent = user ? displayName(user) : '';

    if (el.tgWidget) el.tgWidget.hidden = Boolean(user);
    if (el.tgConsent) {
      const box = el.tgConsent.closest('.consent');
      if (box) box.hidden = Boolean(user);
    }
    if (el.tgNote) {
      el.tgNote.textContent = user
        ? (user.telegram_id ? t('co.tgSigned') : t('co.tgAccountNote'))
        : (tgReady ? t('co.tgNote') : t('co.tgUnavailable'));
    }
    if (!user) setStatus(el.tgStatus, '');

    if (el.accGuest) el.accGuest.hidden = Boolean(user);
    if (el.accUser) el.accUser.hidden = !user;
    if (user) {
      if (el.accName) el.accName.textContent = displayName(user);
      if (el.accMeta) {
        el.accMeta.textContent = user.email
          ? user.email
          : (user.telegram_username ? '@' + user.telegram_username : t('acc.tgAccount'));
      }
    }
  }

  function authErrorText(error) {
    const map = {
      bad_email: 'co.emailBad',
      weak_password: 'co.passwordWeak',
      email_taken: 'co.emailTaken',
      invalid_credentials: 'co.badCreds',
      too_many_requests: 'co.tooMany',
      consent_required: 'co.consentNeeded'
    };
    return t(map[error.code] || 'co.error');
  }

  function authFields() {
    const email = el.authEmail ? el.authEmail.value.trim() : '';
    const password = el.authPassword ? el.authPassword.value : '';
    if (!el.consent || !el.consent.checked) {
      setStatus(el.authStatus, t('co.consentNeeded'), 'error');
      if (el.consent) el.consent.focus();
      return null;
    }
    return { email: email, password: password, consent: true };
  }

  async function submitAuth(kind) {
    const body = authFields();
    if (!body) return;
    if (state.busy) return;
    state.busy = true;
    setStatus(el.authStatus, t('co.pleaseWait'));
    try {
      const data = await api('/api/auth/' + kind, { method: 'POST', body: body });
      state.user = data.user || null;
      if (el.authPassword) el.authPassword.value = '';
      renderAuth();
      setStatus(el.authStatus, t('co.authOk'), 'ok');
      await loadOrders();
    } catch (error) {
      setStatus(el.authStatus, authErrorText(error), 'error');
    } finally {
      state.busy = false;
    }
  }

  async function logout() {
    try { await api('/api/auth/logout', { method: 'POST' }); } catch (e) { /* всё равно чистим */ }
    state.user = null;
    state.orders = [];
    renderAuth();
    renderOrders();
    setStatus(el.authStatus, '');
    setStatus(el.accStatus, '');
  }

  async function loadMe() {
    try {
      const data = await api('/api/auth/me');
      state.user = data.user || null;
      if (!state.health && data.telegram_login !== undefined) {
        state.health = { telegram_login: Boolean(data.telegram_login), bot: data.bot };
      }
    } catch (e) {
      state.user = null;
    }
    renderAuth();
    if (state.user) await loadOrders();
  }

  async function loadOrders() {
    if (!state.user) {
      state.orders = [];
      renderOrders();
      return;
    }
    try {
      const data = await api('/api/orders');
      state.orders = Array.isArray(data.orders) ? data.orders : [];
    } catch (e) {
      state.orders = [];
    }
    renderOrders();
  }

  function downloadUrl(order) {
    if (!order || !order.key || !order.key.download_url) return '#';
    const url = order.key.download_url;
    return url.replace(/([?&])lang=[^&]*/, '$1lang=' + langCode());
  }

  function pluralMonths(months) {
    if (langCode() === 'en') return months + (months === 1 ? ' month' : ' months');
    return months + ' мес.';
  }

  function copyText(text, statusNode) {
    if (!text) return;
    const done = function () { setStatus(statusNode, t('co.copied'), 'ok'); };
    const fail = function () { setStatus(statusNode, t('co.copyFailed'), 'error'); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(fail);
      return;
    }
    const area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    try {
      document.execCommand('copy') ? done() : fail();
    } catch (e) {
      fail();
    }
    document.body.removeChild(area);
  }

  function renderOrders() {
    if (!el.accList) return;
    el.accList.innerHTML = '';

    const user = state.user;
    if (!user) {
      if (el.accEmpty) el.accEmpty.hidden = true;
      return;
    }

    const list = state.orders || [];
    if (el.accEmpty) el.accEmpty.hidden = list.length > 0;

    list.forEach(function (order) {
      const paid = order.status === 'paid';
      const hasKey = paid && order.key && order.key.sub_url;

      const card = document.createElement('article');
      card.className = 'keys__item';

      const head = document.createElement('div');
      head.className = 'keys__head';

      const title = document.createElement('span');
      title.className = 'keys__title';
      title.textContent = planTitle(order.plan_id);
      head.appendChild(title);

      const pill = document.createElement('span');
      pill.className = 'pill ' + (paid ? 'pill--paid' : 'pill--pending');
      pill.textContent = paid ? t('co.paid') : t('acc.pending');
      head.appendChild(pill);

      card.appendChild(head);

      const meta = document.createElement('p');
      meta.className = 'keys__meta';
      let text = order.id;
      if (hasKey && order.key.valid_until) {
        text += ' · ' + t('acc.validUntil') + ' ' + fmtDate(order.key.valid_until);
      } else {
        text += ' · ' + pluralMonths(order.months) + ' · ' + money(order.price);
      }
      meta.textContent = text;
      card.appendChild(meta);

      const actions = document.createElement('div');
      actions.className = 'keys__actions';

      if (hasKey) {
        const download = document.createElement('a');
        download.className = 'btn btn--ghost btn--sm';
        download.href = downloadUrl(order);
        download.setAttribute('download', '');
        download.textContent = t('acc.download');
        actions.appendChild(download);

        const copy = document.createElement('button');
        copy.type = 'button';
        copy.className = 'link-btn';
        copy.textContent = t('acc.copy');
        copy.addEventListener('click', function () {
          copyText(order.key.sub_url, el.accStatus);
        });
        actions.appendChild(copy);
      } else if (order.status === 'pending') {
        const resume = document.createElement('button');
        resume.type = 'button';
        resume.className = 'btn btn--ghost btn--sm';
        resume.textContent = t('acc.continue');
        resume.addEventListener('click', function () {
          state.token = '';
          showPayment(order);
        });
        actions.appendChild(resume);
      }

      if (actions.children.length) card.appendChild(actions);
      el.accList.appendChild(card);
    });
  }

  /* ---------------------- ЗАКАЗ ---------------------- */

  function setPlan(planId) {
    state.planId = planId;
    state.planPrice = PRICE[planId] || 0;
    if (el.orderPlan) el.orderPlan.textContent = planTitle(planId);
    if (el.orderAmount) el.orderAmount.textContent = money(state.planPrice);
    if (el.startPaySum) el.startPaySum.textContent = money(state.planPrice);
  }

  function showCheckout(planId) {
    setPlan(planId);
    if (el.checkout) el.checkout.hidden = false;
    if (el.payment) el.payment.hidden = true;
    if (el.done) el.done.hidden = true;
    setStatus(el.checkoutStatus, '');
    applyMethod();
    if (el.checkout) {
      el.checkout.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' });
    }
    if (el.startPay) el.startPay.focus({ preventScroll: true });
  }

  function setMode(mode) {
    state.mode = mode;
    el.segs.forEach(function (button) {
      const active = button.dataset.mode === mode;
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    el.panes.forEach(function (pane) {
      pane.hidden = pane.dataset.pane !== mode;
    });
    if (mode === 'telegram' && !state.user) ensureTgWidget();
  }

  function ensureTgWidget() {
    if (state.tgInjected || !el.tgWidget) return;
    if (!state.health || !state.health.telegram_login) return;
    if (!el.tgConsent || !el.tgConsent.checked) {
      setStatus(el.tgStatus, t('co.tgConsentNeeded'));
      return;
    }
    state.tgInjected = true;
    setStatus(el.tgStatus, '');

    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', state.health.bot || 'xsisetvpnbot');
    script.setAttribute('data-size', 'medium');
    script.setAttribute('data-radius', '18');
    script.setAttribute('data-userpic', 'false');
    script.setAttribute('data-request-access', 'write');
    script.setAttribute('data-auth-url', window.location.origin + '/api/auth/telegram/callback');
    el.tgWidget.appendChild(script);
  }

  function applyMethod() {
    el.payRadios.forEach(function (radio) {
      if (radio.checked) state.method = radio.value;
    });
    if (el.assetField) el.assetField.hidden = state.method !== 'cryptobot';
    if (el.asset) state.asset = el.asset.value || 'USDT';
  }

  function applyPaymentAvailability() {
    const payments = (state.health && state.health.payments) || {};
    const available = { cryptobot: payments.cryptobot !== false, platega: payments.platega !== false };

    if (payments.assets && payments.assets.length && el.asset) {
      const current = el.asset.value;
      el.asset.innerHTML = '';
      payments.assets.forEach(function (asset) {
        const option = document.createElement('option');
        option.value = asset;
        option.textContent = asset;
        el.asset.appendChild(option);
      });
      if (payments.assets.indexOf(current) !== -1) el.asset.value = current;
    }

    let selectedAvailable = available[state.method];
    el.payLabels.forEach(function (label) {
      const radio = label.querySelector('input[name="payMethod"]');
      if (!radio) return;
      const on = available[radio.value] !== false;
      label.hidden = !on;
      if (!on && radio.checked) radio.checked = false;
    });

    if (!selectedAvailable) {
      el.payRadios.forEach(function (radio) {
        if (!radio.checked && available[radio.value] !== false) {
          radio.checked = true;
          state.method = radio.value;
          selectedAvailable = true;
        }
      });
    }
    applyMethod();
  }

  function setPayPill(status) {
    if (!el.orderStatus) return;
    const map = { pending: 'pill--pending', paid: 'pill--paid', failed: 'pill--failed', expired: 'pill--expired' };
    const label = status === 'paid' ? t('co.paid')
      : status === 'failed' ? t('co.failed')
        : status === 'expired' ? t('co.expired')
          : t('co.pending');
    el.orderStatus.className = 'pill ' + (map[status] || 'pill--pending');
    el.orderStatus.textContent = label;
  }

  function fillPayment(order) {
    if (el.payOrderId) el.payOrderId.textContent = order.id;
    if (el.payPlan) el.payPlan.textContent = planTitle(order.plan_id);
    if (el.payAmount) el.payAmount.textContent = money(order.price);
    setPayPill(order.status);
  }

  function showPayment(order, token) {
    if (!order) return;
    if (token !== undefined) state.token = token || '';
    state.order = order;

    if (el.checkout) el.checkout.hidden = true;
    if (el.done) el.done.hidden = true;
    if (el.payment) el.payment.hidden = false;

    fillPayment(order);
    setStatus(el.payStatus, '');

    const pending = order.status === 'pending';
    const closed = order.status === 'failed' || order.status === 'expired';

    if (el.payHint) {
      el.payHint.textContent = closed ? t('co.closedHint')
        : order.status === 'paid' ? t('co.issuing')
          : t('co.payHint');
    }
    if (el.openPay) {
      el.openPay.hidden = !pending || !order.pay_url;
      el.openPay.href = order.pay_url || '#';
    }
    if (el.check) el.check.hidden = !pending;
    if (el.demo) el.demo.hidden = !(state.demo && pending);
    if (el.cancelPay) el.cancelPay.hidden = !pending;

    if (pending || (order.status === 'paid' && !order.key)) {
      startPolling();
    } else {
      stopPolling();
    }

    if (order.status === 'paid' && order.key) {
      showDone(order);
      return;
    }

    if (el.payment) {
      el.payment.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' });
    }
  }

  function showDone(order) {
    if (!order || !order.key) return;
    state.order = order;
    stopPolling();

    if (el.checkout) el.checkout.hidden = true;
    if (el.payment) el.payment.hidden = true;
    if (el.done) el.done.hidden = false;

    if (el.doneId) el.doneId.textContent = order.id;
    if (el.donePlan) el.donePlan.textContent = planTitle(order.plan_id);
    if (el.doneValid) el.doneValid.textContent = fmtDate(order.key.valid_until);
    if (el.doneKey) el.doneKey.textContent = order.key.sub_url;
    if (el.download) el.download.href = downloadUrl(order);
    setStatus(el.doneStatus, t('co.saved'), 'ok');

    if (el.done) {
      el.done.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' });
    }

    if (state.user) loadOrders();
  }

  function startPolling() {
    stopPolling();
    state.timer = window.setInterval(function () {
      if (!state.busy) refreshOrder(false);
    }, 4000);
  }

  function stopPolling() {
    if (state.timer) {
      window.clearInterval(state.timer);
      state.timer = null;
    }
  }

  async function refreshOrder(manual) {
    if (!state.order || state.busy) return;
    state.busy = true;
    if (manual) setStatus(el.payStatus, t('co.checking'));

    try {
      const data = await api('/api/orders/' + encodeURIComponent(state.order.id) + tokenQuery());
      const order = data.order;
      if (!order) throw new Error('bad_payload');
      state.order = order;

      if (order.status === 'paid' && order.key) {
        showDone(order);
        return;
      }

      fillPayment(order);

      if (order.status === 'failed' || order.status === 'expired') {
        stopPolling();
        if (el.openPay) el.openPay.hidden = true;
        if (el.check) el.check.hidden = true;
        if (el.demo) el.demo.hidden = true;
        if (el.cancelPay) el.cancelPay.hidden = true;
        if (el.payHint) el.payHint.textContent = t('co.closedHint');
        setStatus(el.payStatus, t('co.closedStatus'), 'error');
        return;
      }

      if (order.status === 'paid') {
        if (el.payHint) el.payHint.textContent = t('co.issuing');
        if (el.check) el.check.hidden = true;
        if (el.openPay) el.openPay.hidden = true;
        if (el.demo) el.demo.hidden = true;
        setStatus(el.payStatus, t('co.issuing'), 'ok');
        startPolling();
        return;
      }

      if (manual) setStatus(el.payStatus, t('co.stillPending'));
    } catch (error) {
      if (error.status === 404) {
        resetOrder();
        setStatus(el.checkoutStatus, t('co.notFound'), 'error');
        return;
      }
      if (manual) setStatus(el.payStatus, t('co.offline'), 'error');
    } finally {
      state.busy = false;
    }
  }

  function orderErrorText(error) {
    const map = {
      consent_required: 'co.consentNeeded',
      unknown_asset: 'co.payUnavailable',
      cryptobot_unavailable: 'co.payUnavailable',
      platega_unavailable: 'co.payUnavailable',
      invoice_failed: 'co.invoiceFailed',
      too_many_orders: 'co.tooMany',
      demo_disabled: 'co.error'
    };
    return t(map[error.code] || 'co.error');
  }

  async function createOrder() {
    if (state.busy) return;
    if (!state.planId) return;
    if (state.mode === 'email' && !state.user) {
      setStatus(el.checkoutStatus, t('co.signInFirst'), 'error');
      return;
    }
    if (state.mode === 'telegram' && !state.user) {
      setStatus(el.checkoutStatus, t('co.tgSignInFirst'), 'error');
      return;
    }
    if (!el.consent || !el.consent.checked) {
      setStatus(el.checkoutStatus, t('co.consentNeeded'), 'error');
      if (el.consent) el.consent.focus();
      return;
    }

    state.busy = true;
    if (el.startPay) el.startPay.disabled = true;
    setStatus(el.checkoutStatus, t('co.creating'));

    const body = {
      plan_id: state.planId,
      method: state.method,
      consent: true
    };
    if (state.method === 'cryptobot') body.asset = state.asset;

    try {
      const data = await api('/api/orders', { method: 'POST', body: body });
      if (!data.order) throw new Error('bad_payload');
      state.order = data.order;
      state.token = data.token || '';
      saveOrder();
      showPayment(data.order, state.token);
      if (state.user) loadOrders();
    } catch (error) {
      setStatus(el.checkoutStatus, orderErrorText(error), 'error');
    } finally {
      state.busy = false;
      if (el.startPay) el.startPay.disabled = false;
    }
  }

  function saveOrder() {
    if (!state.order) return;
    try {
      localStorage.setItem(ORDER_KEY, JSON.stringify({
        id: state.order.id,
        token: state.token,
        at: Date.now()
      }));
    } catch (e) { /* приватный режим */ }
  }

  function clearOrder() {
    try { localStorage.removeItem(ORDER_KEY); } catch (e) { /* не критично */ }
  }

  function resetOrder() {
    stopPolling();
    state.order = null;
    state.token = '';
    clearOrder();
    if (el.payment) el.payment.hidden = true;
    if (el.done) el.done.hidden = true;
    if (el.checkout) el.checkout.hidden = true;
    setStatus(el.payStatus, '');
    setStatus(el.doneStatus, '');
  }

  async function restoreOrder() {
    let saved = null;
    try { saved = JSON.parse(localStorage.getItem(ORDER_KEY) || 'null'); } catch (e) { saved = null; }
    if (!saved || !saved.id || !saved.token) return;

    state.token = saved.token;
    try {
      const data = await api('/api/orders/' + encodeURIComponent(saved.id) + '?token=' + encodeURIComponent(saved.token));
      const order = data.order;
      if (!order) throw new Error('bad_payload');
      if (order.status === 'paid' && order.key) {
        showDone(order);
      } else if (order.status === 'pending' || order.status === 'paid') {
        showPayment(order, saved.token);
      } else {
        resetOrder();
      }
    } catch (e) {
      resetOrder();
    }
  }

  /* ---------------------- ОБРАБОТЧИКИ ---------------------- */

  el.plans.forEach(function (link) {
    link.addEventListener('click', function (event) {
      event.preventDefault();
      showCheckout(link.dataset.plan);
    });
  });

  el.segs.forEach(function (button) {
    button.addEventListener('click', function () {
      setMode(button.dataset.mode);
    });
  });

  el.payRadios.forEach(function (radio) {
    radio.addEventListener('change', applyMethod);
  });

  if (el.asset) {
    el.asset.addEventListener('change', function () {
      state.asset = el.asset.value;
    });
  }

  if (el.tgConsent) {
    el.tgConsent.addEventListener('change', function () {
      if (el.tgConsent.checked) ensureTgWidget();
      else setStatus(el.tgStatus, t('co.tgConsentNeeded'));
    });
  }

  if (el.startPay) el.startPay.addEventListener('click', createOrder);

  if (el.cancelPlan) {
    el.cancelPlan.addEventListener('click', function () {
      if (el.checkout) el.checkout.hidden = true;
      setStatus(el.checkoutStatus, '');
      const pricing = $('pricing');
      if (pricing) pricing.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
    });
  }

  if (el.check) el.check.addEventListener('click', function () { refreshOrder(true); });

  if (el.demo) {
    el.demo.addEventListener('click', async function () {
      if (!state.order || state.busy) return;
      state.busy = true;
      el.demo.disabled = true;
      setStatus(el.payStatus, t('co.pleaseWait'));
      try {
        const data = await api('/api/orders/' + encodeURIComponent(state.order.id) + '/demo-pay' + tokenQuery(), { method: 'POST' });
        if (data.order) {
          if (data.order.status === 'paid' && data.order.key) showDone(data.order);
          else {
            state.order = data.order;
            fillPayment(data.order);
            startPolling();
          }
        }
      } catch (error) {
        setStatus(el.payStatus, orderErrorText(error), 'error');
      } finally {
        state.busy = false;
        el.demo.disabled = false;
      }
    });
  }

  if (el.cancelPay) {
    el.cancelPay.addEventListener('click', async function () {
      if (!state.order || state.busy) return;
      state.busy = true;
      try {
        await api('/api/orders/' + encodeURIComponent(state.order.id) + '/cancel' + tokenQuery(), { method: 'POST' });
        resetOrder();
        setStatus(el.payStatus, t('co.cancelled'), 'ok');
        if (state.user) loadOrders();
      } catch (error) {
        setStatus(el.payStatus, t('co.cancelFailed'), 'error');
      } finally {
        state.busy = false;
      }
    });
  }

  if (el.newOrder) {
    el.newOrder.addEventListener('click', function () {
      resetOrder();
      const pricing = $('pricing');
      if (pricing) pricing.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
      state.planId = null;
      if (el.checkout) el.checkout.hidden = true;
    });
  }

  if (el.copyKey) {
    el.copyKey.addEventListener('click', function () {
      if (state.order && state.order.key) copyText(state.order.key.sub_url, el.doneStatus);
    });
  }

  if (el.login) el.login.addEventListener('click', function () { submitAuth('login'); });
  if (el.register) el.register.addEventListener('click', function () { submitAuth('register'); });
  if (el.logout) el.logout.addEventListener('click', logout);
  if (el.accLogout) el.accLogout.addEventListener('click', logout);

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible' && state.order && !state.busy) {
      if (state.order.status === 'pending' || (state.order.status === 'paid' && !state.order.key)) {
        refreshOrder(false);
      }
    }
  });

  /* ---------------------- ПЕРЕРИСОВКА ПРИ СМЕНЕ ЯЗЫКА ---------------------- */

  function renderDynamic() {
    if (state.planId) setPlan(state.planId);
    if (state.order) {
      if (state.order.status === 'paid' && state.order.key) {
        if (el.donePlan) el.donePlan.textContent = planTitle(state.order.plan_id);
        if (el.doneValid) el.doneValid.textContent = fmtDate(state.order.key.valid_until);
      } else {
        fillPayment(state.order);
        if (el.payHint) {
          el.payHint.textContent = state.order.status === 'paid' ? t('co.issuing')
            : state.order.status === 'failed' || state.order.status === 'expired' ? t('co.closedHint')
              : t('co.payHint');
        }
      }
    }
    renderAuth();
    renderOrders();
    applyPaymentAvailability();
    if (state.mode === 'telegram' && !state.user) ensureTgWidget();
  }

  /* ---------------------- СТАРТ ---------------------- */

  let savedLang = 'ru';
  try { savedLang = localStorage.getItem(LANG_KEY) || 'ru'; } catch (e) { /* не критично */ }
  applyLang(savedLang === 'en' ? 'en' : 'ru');
  setMode('anon');

  (async function boot() {
    try {
      state.health = await api('/api/health');
      state.demo = Boolean(state.health.demo);
    } catch (e) {
      state.health = null;
      state.demo = false;
    }

    applyPaymentAvailability();
    renderAuth();

    await loadMe();

    const params = new URLSearchParams(window.location.search);
    const authResult = params.get('auth');
    if (authResult) {
      try {
        const clean = window.location.pathname + window.location.hash;
        window.history.replaceState({}, '', clean);
      } catch (e) { /* не критично */ }
      if (authResult === 'ok') {
        await loadMe();
        setStatus(el.accStatus, t('acc.authOk'), 'ok');
      } else {
        setStatus(el.accStatus, t('acc.authFail'), 'error');
      }
    }

    await restoreOrder();
  })();

})();
