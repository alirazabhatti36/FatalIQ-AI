(function () {
  var scriptTag = document.currentScript;
  var adsenseClient = (scriptTag && scriptTag.getAttribute('data-adsense-client')) || 'ca-pub-1373118680696037';
  var gaMeasurementId = (scriptTag && scriptTag.getAttribute('data-ga-measurement-id')) || 'G-06PT7VHV1Q';
  var consentKey = 'atk360_cookie_consent';

  function getConsent() {
    try {
      return localStorage.getItem(consentKey);
    } catch (_e) {
      return null;
    }
  }

  function setConsent(value) {
    try {
      localStorage.setItem(consentKey, value);
    } catch (_e) {
      // Ignore storage errors in restricted browser modes.
    }
  }

  function loadScriptOnce(src, attrs) {
    if (document.querySelector('script[src="' + src + '"]')) {
      return;
    }
    var s = document.createElement('script');
    s.src = src;
    s.async = true;
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        s.setAttribute(k, attrs[k]);
      });
    }
    document.head.appendChild(s);
  }

  function enableTrackingAndAds() {
    if (window.__atk360TrackingLoaded) {
      return;
    }
    window.__atk360TrackingLoaded = true;

    loadScriptOnce(
      'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + encodeURIComponent(adsenseClient),
      { crossorigin: 'anonymous' }
    );

    loadScriptOnce('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(gaMeasurementId));

    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', gaMeasurementId);
  }

  function removeBanner() {
    var existing = document.getElementById('atk360-consent-banner');
    if (existing) {
      existing.remove();
    }
  }

  function saveAndApply(choice) {
    setConsent(choice);
    removeBanner();
    if (choice === 'granted') {
      enableTrackingAndAds();
    }
  }

  function injectBanner() {
    if (document.getElementById('atk360-consent-banner')) {
      return;
    }

    var style = document.createElement('style');
    style.textContent = '' +
      '#atk360-consent-banner{position:fixed;left:12px;right:12px;bottom:12px;z-index:9999;background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:12px;box-shadow:0 10px 24px rgba(0,0,0,.28);padding:12px;display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;font-family:Segoe UI,system-ui,sans-serif}' +
      '#atk360-consent-banner p{margin:0;font-size:13px;line-height:1.45;max-width:780px}' +
      '#atk360-consent-banner .atk360-actions{display:flex;gap:8px;flex-wrap:wrap}' +
      '#atk360-consent-banner button{border:0;border-radius:8px;padding:8px 12px;font-size:12px;font-weight:600;cursor:pointer}' +
      '#atk360-consent-accept{background:#22c55e;color:#052e16}' +
      '#atk360-consent-reject{background:#334155;color:#e2e8f0}' +
      '#atk360-consent-banner a{color:#93c5fd;text-decoration:underline}' +
      '@media (max-width:640px){#atk360-consent-banner{left:8px;right:8px;bottom:8px;padding:10px}#atk360-consent-banner p{font-size:12px}}';
    document.head.appendChild(style);

    var banner = document.createElement('div');
    banner.id = 'atk360-consent-banner';
    banner.innerHTML =
      '<p>We use cookies for analytics and ads personalization. You can accept or reject non-essential cookies. Read our <a href="/privacy-policy">Privacy Policy</a>.</p>' +
      '<div class="atk360-actions">' +
      '<button id="atk360-consent-reject" type="button">Reject</button>' +
      '<button id="atk360-consent-accept" type="button">Accept</button>' +
      '</div>';

    document.body.appendChild(banner);

    document.getElementById('atk360-consent-accept').addEventListener('click', function () {
      saveAndApply('granted');
    });
    document.getElementById('atk360-consent-reject').addEventListener('click', function () {
      saveAndApply('denied');
    });
  }

  function start() {
    var consent = getConsent();
    if (consent === 'granted') {
      enableTrackingAndAds();
      return;
    }
    if (consent === 'denied') {
      return;
    }
    injectBanner();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }

  window.openCookieSettings = function () {
    try {
      localStorage.removeItem(consentKey);
    } catch (_e) {}
    injectBanner();
  };
})();
