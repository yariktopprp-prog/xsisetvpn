/* =========================================================
   xsiset vpn: клиентская логика без регистрации.
   Чистая анонимная покупка: тариф -> оплата -> ключ + автоустановка.
   ========================================================= */

(function () {
  'use strict';

  const I18N = {
    ru: {
      'meta.title': 'xsiset vpn · VPN без границ',
      'meta.desc': 'xsiset vpn: пять серверов в Европе, обход белых списков, оплата картой и криптой на сайте, ключ сразу после оплаты.',
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
      'nav.faq': 'Вопросы',
      'nav.cta': 'Подключиться',
      'nav.support': 'Поддержка',

      'hero.live': '5 серверов онлайн',
      'hero.badge': 'обход белых списков',
      'hero.t1': 'Интернет',
      'hero.t2': 'без границ.',
      'hero.text': 'Пять серверов в Европе. Без регистрации: оплата на сайте, ключ сразу на экране и в .txt.',
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
      'feat.pay.d': 'CryptoBot: USDT, TRX, TON. Platega: карта и СБП. Счёт создаётся прямо на сайте.',
      'feat.auto.t': 'Ключ сразу',
      'feat.auto.d': 'После оплаты сайт сам создаёт VLESS-доступ на всех пяти серверах.',
      'feat.renew.t': 'Файл и кнопка установки',
      'feat.renew.d': 'Ключ скачивается файлом .txt и устанавливается в приложение кликом по кнопке.',
      'feat.help.t': 'Поддержка',
      'feat.help.d': 'Вопросы по подключению — в @xsisetvpnbot.',

      'how.title': 'Три шага',
      'how.text': 'От выбора тарифа до рабочего ключа — пара минут.',
      'how.s1.t': 'Выберите тариф',
      'how.s1.d': '1, 3, 6 или 12 месяцев. Все пять серверов включены.',
      'how.s2.t': 'Оплатите на сайте',
      'how.s2.d': 'CryptoBot или Platega: карта, СБП, USDT, TRX, TON.',
      'how.s3.t': 'Установите ключ',
      'how.s3.d': 'Нажмите «Открыть подписку» для авто-импорта или сохраните файл .txt.',

      'price.title': 'Тарифы',
      'price.text': 'Один тариф — все пять серверов. Никаких регистраций: ключ выдаётся сразу.',
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
      'co.method': 'Способ оплаты',
      'co.cryptoSub': 'USDT, TRX, TON',
      'co.plategaSub': 'Карта, СБП',
      'co.asset': 'Монета',
      'co.consentText': 'Я согласен с',
      'co.termsLink': 'условиями сервиса',
      'co.and': 'и',
      'co.privacyLink': 'политикой конфиденциальности',
      'co.payNow': 'Перейти к оплате',
      'co.creating': 'Создаём заказ и счёт…',
      'co.consentNeeded': 'Необходимо подтвердить согласие с условиями.',
      'co.payUnavailable': 'Способ оплаты временно недоступен.',
      'co.invoiceFailed': 'Не удалось выставить счёт. Попробуйте другой способ.',
      'co.error': 'Произошла ошибка. Попробуйте ещё раз.',
      'co.offline': 'Сервер временно недоступен.',
      'co.notFound': 'Заказ не найден.',

      'co.payLabel': 'Оплата',
      'co.awaiting': 'Ожидает оплаты',
      'co.pending': 'Ожидает оплаты',
      'co.paid': 'Оплачено',
      'co.failed': 'Ошибка оплаты',
      'co.expired': 'Истёк',
      'co.number': 'Номер заказа',
      'co.plan': 'Тариф',
      'co.sum': 'Сумма',
      'co.validUntil': 'Действует до',
      'co.payHint': 'Откройте оплату и завершите платёж. Статус обновится автоматически.',
      'co.issuing': 'Оплата получена. Выпускаем VLESS-ключ…',
      'co.openPay': 'Перейти к оплате',
      'co.check': 'Проверить оплату',
      'co.cancelPay': 'Отменить заказ',
      'co.checking': 'Проверяем статус…',
      'co.stillPending': 'Оплата пока не поступила. Повторите через минуту.',
      'co.closedHint': 'Заказ закрыт. Создайте новый.',
      'co.closedStatus': 'Заказ закрыт.',
      'co.cancelled': 'Заказ отменён.',
      'co.cancelFailed': 'Не удалось отменить заказ.',

      'co.doneLabel': 'Ключ готов',
      'co.doneTitle': 'Доступ активирован',
      'co.doneHint': 'Ключ — это ссылка-подписка. Нажмите «Открыть подписку» для перехода или сохраните файл с ключом .txt.',
      'co.install': 'Открыть подписку',
      'co.download': 'Файл с ключом (.txt)',
      'co.copy': 'Скопировать ссылку',
      'co.support': 'Поддержка',
      'co.copied': 'Ссылка-ключ скопирована в буфер обмена.',
      'co.copyFailed': 'Выделите и скопируйте ссылку вручную.',
      'co.newOrder': 'Купить ещё один ключ',
      'co.saved': 'Ключ активирован! Сохраните файл или скопируйте ссылку.',

      'pill.title': 'Приватность по умолчанию',
      'pill.badge': 'No-Logs',
      'pill.desc': 'Мы не храним логи активности, не требуем почту или аккаунт и не используем трекеры.',
      'pill.more': 'Подробнее',
      'pill.ok': 'Понятно',

      'faq.title': 'Вопросы',
      'faq.text': 'Коротко о том, как всё устроено.',
      'faq.q1': 'Как проходит оплата?',
      'faq.a1': 'Выбираете тариф и способ оплаты. Сайт создаёт счёт в CryptoBot или Platega, сам проверяет оплату и сразу выдаёт ключ. Регистрация не требуется.',
      'faq.q2': 'Какие способы оплаты есть?',
      'faq.a2': 'CryptoBot принимает USDT, TRX и TON. Platega — банковские карты и СБП. Все расчёты в рублях, комиссия сервиса видна до оплаты.',
      'faq.q3': 'Как подключить VPN после оплаты?',
      'faq.a3': 'Сразу после оплаты появится кнопка «Открыть подписку», которая позволяет скопировать или импортировать данные в клиент (Happ, Streisand, v2rayNG, FoXray). Также можно скачать .txt файл или скопировать ссылку вручную.',
      'faq.q4': 'Есть пробный период?',
      'faq.a4': 'Пробный доступ выдаётся только в Telegram-боте @xsisetvpnbot. На сайте сразу доступна покупка полных тарифов.',
      'faq.q5': 'Что такое обход белых списков?',
      'faq.a5': 'Это специальный отдельный узел для случаев, когда обычные протоколы VPN блокируются по белым спискам провайдеров. Он включён во все тарифы.',

      'cta.title': 'Подключиться',
      'cta.text': 'Выберите тариф и оплатите на сайте. Если возникнут вопросы, напишите в поддержку.',
      'cta.bot': 'Открыть @xsisetvpnbot',
      'cta.support': 'Поддержка @hkpde',
      'ftr.support': 'Поддержка',
      'ftr.mail': 'Почта',
      'ftr.terms': 'Условия',
      'ftr.privacy': 'Политика'
    },

    en: {
      'meta.title': 'xsiset vpn · VPN without borders',
      'meta.desc': 'xsiset vpn: five servers in Europe, whitelist bypass, card and crypto payment on the site, instant key delivery.',
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
      'nav.faq': 'FAQ',
      'nav.cta': 'Get started',
      'nav.support': 'Support',

      'hero.live': '5 servers online',
      'hero.badge': 'whitelist bypass',
      'hero.t1': 'The internet',
      'hero.t2': 'without borders.',
      'hero.text': 'Five servers in Europe. No registration: pay on the site, get the key instantly.',
      'hero.cta1': 'Choose a plan',
      'hero.cta2': 'Open the bot',
      'term.state': '5 servers',

      'servers.title': 'Servers in Europe',
      'servers.text': 'One plan covers all five nodes. Dedicated server for whitelist bypass.',
      'servers.nl': 'Netherlands',
      'servers.nl.d': 'Direct internet access through the Netherlands.',
      'servers.se': 'Sweden',
      'servers.se.d': 'Two separate servers in Sweden.',
      'servers.de': 'Germany',
      'servers.de.d': 'Direct internet access through Germany.',
      'servers.wl': 'Whitelist bypass',
      'servers.wl.d': 'For networks where regular VPNs are blocked by whitelist rules.',
      'servers.one': '1 server',
      'servers.two': '2 servers',
      'node.online': 'available',

      'feat.title': 'All on the site',
      'feat.text': 'Choose a plan, pay, receive the key and support — no middleman.',
      'feat.pay.t': 'Card & Crypto',
      'feat.pay.d': 'CryptoBot: USDT, TRX, TON. Platega: bank cards & SBP. The invoice is generated on site.',
      'feat.auto.t': 'Instant key',
      'feat.auto.d': 'After payment the system provisions VLESS access across all five nodes automatically.',
      'feat.renew.t': 'Key file & 1-click setup',
      'feat.renew.d': 'Download a .txt file with full instructions or import the link into your app.',
      'feat.help.t': 'Support',
      'feat.help.d': 'Setup assistance in @xsisetvpnbot.',

      'how.title': 'Three steps',
      'how.text': 'From choosing a plan to a working connection in a couple of minutes.',
      'how.s1.t': 'Choose a plan',
      'how.s1.d': '1, 3, 6 or 12 months. All five servers included.',
      'how.s2.t': 'Pay on site',
      'how.s2.d': 'CryptoBot or Platega: card, SBP, USDT, TRX, TON.',
      'how.s3.t': 'Install your key',
      'how.s3.d': 'Click "Open subscription" to import into client or save the .txt file.',

      'price.title': 'Pricing',
      'price.text': 'One plan covers all five servers. No accounts or registrations required.',
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
      'co.method': 'Payment method',
      'co.cryptoSub': 'USDT, TRX, TON',
      'co.plategaSub': 'Card, SBP',
      'co.asset': 'Coin',
      'co.consentText': 'I agree with',
      'co.termsLink': 'terms of service',
      'co.and': 'and',
      'co.privacyLink': 'privacy policy',
      'co.payNow': 'Proceed to payment',
      'co.creating': 'Creating invoice…',
      'co.consentNeeded': 'Please confirm agreement with terms of service.',
      'co.payUnavailable': 'Payment method is temporarily unavailable.',
      'co.invoiceFailed': 'Failed to create invoice.',
      'co.error': 'An error occurred. Please try again.',
      'co.offline': 'Server is temporarily offline.',
      'co.notFound': 'Order not found.',

      'co.payLabel': 'Payment',
      'co.awaiting': 'Awaiting payment',
      'co.pending': 'Awaiting payment',
      'co.paid': 'Paid',
      'co.failed': 'Payment failed',
      'co.expired': 'Expired',
      'co.number': 'Order ID',
      'co.plan': 'Plan',
      'co.sum': 'Total',
      'co.validUntil': 'Valid until',
      'co.payHint': 'Complete payment on the provider page. Status updates automatically.',
      'co.issuing': 'Payment confirmed. Issuing your VLESS key…',
      'co.openPay': 'Go to payment',
      'co.check': 'Check payment',
      'co.cancelPay': 'Cancel order',
      'co.checking': 'Checking status…',
      'co.stillPending': 'Payment not received yet. Try again in a minute.',
      'co.closedHint': 'Order closed. Please create a new one.',
      'co.closedStatus': 'Order closed.',
      'co.cancelled': 'Order cancelled.',
      'co.cancelFailed': 'Could not cancel order.',

      'co.doneLabel': 'Key ready',
      'co.doneTitle': 'Access activated',
      'co.doneHint': 'Your key is a subscription link. Click "Open subscription" to view or download the key file (.txt).',
      'co.install': 'Open subscription',
      'co.download': 'Key file (.txt)',
      'co.copy': 'Copy link',
      'co.support': 'Support',
      'co.copied': 'Key link copied to clipboard.',
      'co.copyFailed': 'Please copy the key manually.',
      'co.newOrder': 'Buy another key',
      'co.saved': 'Key activated! Save the file or copy your link.',

      'pill.title': 'Privacy by default',
      'pill.badge': 'No-Logs',
      'pill.desc': 'We do not log activity, require no accounts or email, and run no trackers.',
      'pill.more': 'Learn more',
      'pill.ok': 'Got it',

      'faq.title': 'Questions',
      'faq.text': 'The short version of how it works.',
      'faq.q1': 'How does payment work?',
      'faq.a1': 'Pick a plan and payment method. The site creates an invoice in CryptoBot or Platega and issues your key right away without registration.',
      'faq.q2': 'Which payment methods are available?',
      'faq.a2': 'CryptoBot accepts USDT, TRX and TON. Platega accepts bank cards and SBP.',
      'faq.q3': 'How do I connect after payment?',
      'faq.a3': 'Click "Open subscription" to view the config, or download the .txt file and copy the link.',
      'faq.q4': 'Is there a free trial?',
      'faq.a4': 'Trial access is available only in the @xsisetvpnbot Telegram bot.',
      'faq.q5': 'What is whitelist bypass?',
      'faq.a5': 'A dedicated server designed for restricted networks where regular VPN protocols are blocked.',

      'cta.title': 'Get connected',
      'cta.text': 'Choose a plan and pay on the site. If you need help, contact support.',
      'cta.bot': 'Open @xsisetvpnbot',
      'cta.support': 'Support @hkpde',
      'ftr.support': 'Support',
      'ftr.mail': 'Email',
      'ftr.terms': 'Terms',
      'ftr.privacy': 'Privacy'
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

    // Переводим уже показанные статусные сообщения, если они есть в словаре.
    [el.checkoutStatus, el.payStatus, el.doneStatus].forEach(function (node) {
      if (!node || !node.textContent) return;
      const current = node.textContent.trim();
      const source = I18N.ru;
      for (const key in source) {
        if (source[key] === current && d[key]) {
          node.textContent = d[key];
          break;
        }
      }
    });

    try { localStorage.setItem(LANG_KEY, code); } catch (e) { }

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
      try { localStorage.setItem(THEME_KEY, theme); } catch (e) { }
    }
  }

  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      setTheme(root.getAttribute('data-theme') === 'light' ? 'dark' : 'light', true);
    });
  }

  setTheme(root.getAttribute('data-theme') === 'light' ? 'light' : 'dark', false);

  /* ---------------------- СКРОЛЛ ШАПКИ ---------------------- */

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
  }

  /* ---------------------- REVEAL ---------------------- */

  const reveals = document.querySelectorAll('.reveal');

  function showReveal(el) {
    el.classList.add('is-in');
    setTimeout(function () { el.classList.add('is-settled'); }, 900);
  }

  if (reduceMotion || !('IntersectionObserver' in window)) {
    reveals.forEach(showReveal);
  } else {
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          showReveal(entry.target);
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });

    reveals.forEach(function (el) { io.observe(el); });
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
    cancelPay: $('cancelPayBtn'),
    payStatus: $('payStatus'),
    doneId: $('doneId'),
    donePlan: $('donePlan'),
    doneValid: $('doneValid'),
    doneKey: $('doneKey'),
    installBtn: $('installBtn'),
    download: $('downloadBtn'),
    copyKey: $('copyKeyBtn'),
    newOrder: $('newOrderBtn'),
    doneStatus: $('doneStatus')
  };

  /* ---------------------- СОСТОЯНИЕ ---------------------- */

  const state = {
    planId: null,
    planPrice: 0,
    method: 'cryptobot',
    asset: 'USDT',
    order: null,
    token: '',
    timer: null,
    busy: false,
    health: null
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

  function fallbackCopy(text, done, fail) {
    const area = document.createElement('textarea');
    area.value = text;
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.focus();
    area.select();
    try {
      document.execCommand('copy') ? done() : fail();
    } catch (e) {
      fail();
    }
    document.body.removeChild(area);
  }

  function copyText(text, statusNode) {
    if (!text) return;
    const done = function () { setStatus(statusNode, t('co.copied'), 'ok'); };
    const fail = function () { setStatus(statusNode, t('co.copyFailed'), 'error'); };

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(function () {
        fallbackCopy(text, done, fail);
      });
    } else {
      fallbackCopy(text, done, fail);
    }
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
  }

  function applyMethod() {
    el.payRadios.forEach(function (radio) {
      if (radio.checked) state.method = radio.value;
    });

    if (el.assetField) {
      const isCrypto = (state.method === 'cryptobot');
      el.assetField.hidden = !isCrypto;
      el.assetField.style.display = isCrypto ? 'grid' : 'none';
    }
    if (el.asset) state.asset = el.asset.value || 'USDT';
  }

  function applyPaymentAvailability() {
    const payments = (state.health && state.health.payments) || {};
    const available = {
      cryptobot: payments.cryptobot !== false,
      platega: payments.platega !== false
    };

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

  function refreshDownload() {
    if (!el.download || !state.order || !state.order.key) return;
    const baseArg = state.token ? '?token=' + encodeURIComponent(state.token) + '&' : '?';
    el.download.href = '/api/orders/' + encodeURIComponent(state.order.id) + '/key.txt' + baseArg + 'lang=' + langCode();
    el.download.target = '_blank';
    el.download.rel = 'noopener';
    el.download.setAttribute('download', 'xsiset-vpn-' + state.order.id + '.txt');
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

    refreshDownload();

    if (el.installBtn) {
      el.installBtn.href = order.key.sub_url;
      el.installBtn.target = '_blank';
      el.installBtn.rel = 'noopener';
    }

    setStatus(el.doneStatus, t('co.saved'), 'ok');

    if (el.done) {
      el.done.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' });
    }
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
        if (el.cancelPay) el.cancelPay.hidden = true;
        if (el.payHint) el.payHint.textContent = t('co.closedHint');
        setStatus(el.payStatus, t('co.closedStatus'), 'error');
        return;
      }

      if (order.status === 'paid') {
        if (el.payHint) el.payHint.textContent = t('co.issuing');
        if (el.check) el.check.hidden = true;
        if (el.openPay) el.openPay.hidden = true;
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
      invoice_failed: 'co.invoiceFailed'
    };
    return t(map[error.code] || 'co.error');
  }

  async function createOrder() {
    if (state.busy) return;
    if (!state.planId) return;
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
    } catch (e) { }
  }

  function clearOrder() {
    try { localStorage.removeItem(ORDER_KEY); } catch (e) { }
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
    try { saved = JSON.parse(localStorage.getItem(ORDER_KEY) || 'null'); } catch (e) { }
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

  el.payRadios.forEach(function (radio) {
    radio.addEventListener('change', applyMethod);
  });

  el.payLabels.forEach(function (label) {
    label.addEventListener('click', function () {
      const radio = label.querySelector('input[name="payMethod"]');
      if (radio) {
        radio.checked = true;
        applyMethod();
      }
    });
  });

  if (el.asset) {
    el.asset.addEventListener('change', function () {
      state.asset = el.asset.value;
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

  if (el.cancelPay) {
    el.cancelPay.addEventListener('click', async function () {
      if (!state.order || state.busy) return;
      state.busy = true;
      try {
        await api('/api/orders/' + encodeURIComponent(state.order.id) + '/cancel' + tokenQuery(), { method: 'POST' });
        resetOrder();
        setStatus(el.payStatus, t('co.cancelled'), 'ok');
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

  function renderDynamic() {
    if (state.planId) setPlan(state.planId);
    if (state.order) {
      if (state.order.status === 'paid' && state.order.key) {
        if (el.donePlan) el.donePlan.textContent = planTitle(state.order.plan_id);
        if (el.doneValid) el.doneValid.textContent = fmtDate(state.order.key.valid_until);
        refreshDownload();
      } else {
        fillPayment(state.order);
      }
    }
    applyPaymentAvailability();
  }

  /* ---------------------- ПЛАШКА ПРИВАТНОСТИ ---------------------- */

  const PRIVACY_DISMISSED_KEY = 'xsisetvpn-privacy-notice';
  const privacyPill = document.getElementById('privacyNotice');
  const privacyBtn = document.getElementById('privacyNoticeBtn');

  try {
    if (localStorage.getItem(PRIVACY_DISMISSED_KEY) === '1' && privacyPill) {
      privacyPill.classList.add('is-hidden');
    }
  } catch (e) { }

  if (privacyBtn && privacyPill) {
    privacyBtn.onclick = function (e) {
      if (e) e.preventDefault();
      privacyPill.style.opacity = '0';
      privacyPill.style.transform = 'translateY(18px)';
      setTimeout(function () {
        privacyPill.classList.add('is-hidden');
      }, 250);
      try {
        localStorage.setItem(PRIVACY_DISMISSED_KEY, '1');
      } catch (err) { }
    };
  }

  /* ---------------------- СТАРТ ---------------------- */

  let savedLang = 'ru';
  try { savedLang = localStorage.getItem(LANG_KEY) || 'ru'; } catch (e) { }
  applyLang(savedLang === 'en' ? 'en' : 'ru');

  (async function boot() {
    try {
      state.health = await api('/api/health');
    } catch (e) {
      state.health = null;
    }

    applyPaymentAvailability();
    await restoreOrder();
  })();

})();