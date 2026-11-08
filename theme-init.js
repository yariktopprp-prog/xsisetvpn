/* Инициализация темы и класса js до отрисовки — вынесено из inline-скрипта ради строгого CSP. */
(function () {
  try {
    if (localStorage.getItem('xsisetvpn-theme') === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    }
  } catch (e) { }
  document.documentElement.className += ' js';
  setTimeout(function () {
    if (!document.documentElement.classList.contains('js-ready')) {
      document.documentElement.classList.add('js-safe');
    }
  }, 2500);
})();
