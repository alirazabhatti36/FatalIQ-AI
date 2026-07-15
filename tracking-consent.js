(function () {
  var scriptTag = document.currentScript;
  var adsenseClient = (scriptTag && scriptTag.getAttribute('data-adsense-client')) || 'ca-pub-1373118680696037';
  var gaMeasurementId = (scriptTag && scriptTag.getAttribute('data-ga-measurement-id')) || 'G-06PT7VHV1Q';
  var consentKey = 'atk360_cookie_prefs';
  var legacyConsentKey = 'atk360_cookie_consent';

  function defaultPrefs() {
    return {
      analytics: false,
      ads: false
    };
  }

  function normalizePrefs(value) {
    if (!value || typeof value !== 'object') {
      return null;
    }
    return {
      analytics: !!value.analytics,
      ads: !!value.ads
    };
  }

  function getStoredPrefs() {
    try {
      var raw = localStorage.getItem(consentKey);
      if (raw) {
        var parsed = JSON.parse(raw);
        var normalized = normalizePrefs(parsed);
        if (normalized) {
          return normalized;
        }
      }

      var legacy = localStorage.getItem(legacyConsentKey);
      if (legacy === 'granted') {
        return { analytics: true, ads: true };
      }
      if (legacy === 'denied') {
        return { analytics: false, ads: false };
      }
    } catch (_e) {
      // Ignore storage errors in restricted browser modes.
    }
    return null;
  }

  function savePrefs(prefs) {
    var normalized = normalizePrefs(prefs) || defaultPrefs();
    try {
      localStorage.setItem(consentKey, JSON.stringify(normalized));
      localStorage.setItem(legacyConsentKey, (normalized.analytics || normalized.ads) ? 'granted' : 'denied');
    } catch (_e) {
      // Ignore storage errors in restricted browser modes.
    }
    return normalized;
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

  function ensureGtagBase() {
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  }

  function applyConsentMode(prefs) {
    ensureGtagBase();
    window.gtag('consent', 'default', {
      ad_storage: prefs.ads ? 'granted' : 'denied',
      analytics_storage: prefs.analytics ? 'granted' : 'denied',
      ad_user_data: prefs.ads ? 'granted' : 'denied',
      ad_personalization: prefs.ads ? 'granted' : 'denied'
    });
  }

  function enableAnalytics() {
    if (!window.__atk360AnalyticsLoaded) {
      loadScriptOnce('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(gaMeasurementId));
      window.__atk360AnalyticsLoaded = true;
    }

    if (window.__atk360GaConfigured) {
      return;
    }

    ensureGtagBase();
    window.gtag('js', new Date());
    window.gtag('config', gaMeasurementId);
    window.__atk360GaConfigured = true;
  }

  function enableAds() {
    if (window.__atk360AdsLoaded) {
      return;
    }

    loadScriptOnce(
      'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + encodeURIComponent(adsenseClient),
      { crossorigin: 'anonymous' }
    );
    window.__atk360AdsLoaded = true;
  }

  function applyPreferences(prefs) {
    applyConsentMode(prefs);
    if (prefs.analytics) {
      enableAnalytics();
    }
    if (prefs.ads) {
      enableAds();
    }
  }

  function removeBanner() {
    var existing = document.getElementById('atk360-consent-banner');
    if (existing) {
      existing.remove();
    }
  }

  function removeModal() {
    var modal = document.getElementById('atk360-consent-modal');
    if (modal) {
      modal.remove();
    }
  }

  function ensureStyle() {
    if (document.getElementById('atk360-consent-style')) {
      return;
    }

    var style = document.createElement('style');
    style.id = 'atk360-consent-style';
    style.textContent = '' +
      '#atk360-consent-banner{position:fixed;left:12px;right:12px;bottom:12px;z-index:9999;background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:12px;box-shadow:0 10px 24px rgba(0,0,0,.28);padding:12px;display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;font-family:Segoe UI,system-ui,sans-serif}' +
      '#atk360-consent-banner p{margin:0;font-size:13px;line-height:1.45;max-width:780px}' +
      '#atk360-consent-banner .atk360-actions{display:flex;gap:8px;flex-wrap:wrap}' +
      '#atk360-consent-banner button{border:0;border-radius:8px;padding:8px 12px;font-size:12px;font-weight:600;cursor:pointer}' +
      '#atk360-consent-accept{background:#22c55e;color:#052e16}' +
      '#atk360-consent-manage{background:#1d4ed8;color:#e0e7ff}' +
      '#atk360-consent-reject{background:#334155;color:#e2e8f0}' +
      '#atk360-consent-banner a{color:#93c5fd;text-decoration:underline}' +
      '#atk360-consent-modal{position:fixed;inset:0;z-index:10000;background:rgba(2,6,23,.66);display:flex;align-items:center;justify-content:center;padding:14px;font-family:Segoe UI,system-ui,sans-serif}' +
      '#atk360-consent-modal .atk360-panel{width:min(560px,100%);background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:14px;box-shadow:0 16px 36px rgba(0,0,0,.35);padding:14px}' +
      '#atk360-consent-modal h3{margin:0 0 8px 0;font-size:16px}' +
      '#atk360-consent-modal p{margin:0 0 10px 0;font-size:13px;color:#cbd5e1;line-height:1.45}' +
      '#atk360-consent-modal .atk360-row{display:flex;justify-content:space-between;gap:10px;background:#1e293b;border:1px solid #334155;border-radius:10px;padding:10px;margin-top:8px}' +
      '#atk360-consent-modal .atk360-row strong{font-size:13px;display:block}' +
      '#atk360-consent-modal .atk360-row span{font-size:12px;color:#94a3b8;display:block;margin-top:2px}' +
      '#atk360-consent-modal .atk360-row input{transform:scale(1.12)}' +
      '#atk360-consent-modal .atk360-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:12px;flex-wrap:wrap}' +
      '#atk360-consent-modal button{border:0;border-radius:8px;padding:8px 12px;font-size:12px;font-weight:600;cursor:pointer}' +
      '#atk360-modal-cancel{background:#334155;color:#e2e8f0}' +
      '#atk360-modal-save{background:#22c55e;color:#052e16}' +
      '#atk360-cookie-settings-btn{position:fixed;right:12px;bottom:12px;z-index:9998;border:1px solid #334155;border-radius:999px;background:#0f172a;color:#e2e8f0;padding:8px 12px;font-size:12px;font-weight:600;cursor:pointer;box-shadow:0 8px 18px rgba(0,0,0,.25)}' +
      '@media (max-width:640px){#atk360-consent-banner{left:8px;right:8px;bottom:8px;padding:10px}#atk360-consent-banner p{font-size:12px}}';
    document.head.appendChild(style);
  }

  function ensureCookieSettingsButton() {
    ensureStyle();
    if (document.getElementById('atk360-cookie-settings-btn')) {
      return;
    }

    var btn = document.createElement('button');
    btn.id = 'atk360-cookie-settings-btn';
    btn.type = 'button';
    btn.textContent = 'Cookie Settings';
    btn.addEventListener('click', function () {
      openPreferencesModal(getStoredPrefs() || defaultPrefs());
    });

    document.body.appendChild(btn);
  }

  function saveAndApplyPrefs(prefs) {
    var normalized = savePrefs(prefs);
    removeBanner();
    removeModal();
    applyPreferences(normalized);
  }

  function openPreferencesModal(initialPrefs) {
    ensureStyle();
    removeModal();

    var prefs = normalizePrefs(initialPrefs) || defaultPrefs();
    var modal = document.createElement('div');
    modal.id = 'atk360-consent-modal';
    modal.innerHTML =
      '<div class="atk360-panel">' +
      '<h3>Cookie Preferences</h3>' +
      '<p>Choose which optional cookies you allow. Essential cookies are always active for core site functions.</p>' +
      '<div class="atk360-row"><div><strong>Analytics</strong><span>Helps us understand traffic and improve the site.</span></div><input id="atk360-pref-analytics" type="checkbox" ' + (prefs.analytics ? 'checked' : '') + '></div>' +
      '<div class="atk360-row"><div><strong>Advertising</strong><span>Enables AdSense and ad personalization controls.</span></div><input id="atk360-pref-ads" type="checkbox" ' + (prefs.ads ? 'checked' : '') + '></div>' +
      '<div class="atk360-actions">' +
      '<button id="atk360-modal-cancel" type="button">Cancel</button>' +
      '<button id="atk360-modal-save" type="button">Save Preferences</button>' +
      '</div>' +
      '</div>';

    document.body.appendChild(modal);

    document.getElementById('atk360-modal-cancel').addEventListener('click', function () {
      removeModal();
    });

    document.getElementById('atk360-modal-save').addEventListener('click', function () {
      saveAndApplyPrefs({
        analytics: !!document.getElementById('atk360-pref-analytics').checked,
        ads: !!document.getElementById('atk360-pref-ads').checked
      });
    });
  }

  function injectBanner() {
    ensureStyle();
    if (document.getElementById('atk360-consent-banner')) {
      return;
    }

    var banner = document.createElement('div');
    banner.id = 'atk360-consent-banner';
    banner.innerHTML =
      '<p>We use cookies for analytics and ads personalization. You can accept, reject, or manage your preferences. Read our <a href="/privacy-policy">Privacy Policy</a>.</p>' +
      '<div class="atk360-actions">' +
      '<button id="atk360-consent-reject" type="button">Reject All</button>' +
      '<button id="atk360-consent-manage" type="button">Manage</button>' +
      '<button id="atk360-consent-accept" type="button">Accept All</button>' +
      '</div>';

    document.body.appendChild(banner);

    document.getElementById('atk360-consent-accept').addEventListener('click', function () {
      saveAndApplyPrefs({ analytics: true, ads: true });
    });

    document.getElementById('atk360-consent-reject').addEventListener('click', function () {
      saveAndApplyPrefs({ analytics: false, ads: false });
    });

    document.getElementById('atk360-consent-manage').addEventListener('click', function () {
      openPreferencesModal(getStoredPrefs() || defaultPrefs());
    });
  }

  function start() {
    ensureCookieSettingsButton();

    var prefs = getStoredPrefs();
    if (prefs) {
      applyPreferences(prefs);
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
    ensureCookieSettingsButton();
    injectBanner();
    openPreferencesModal(getStoredPrefs() || defaultPrefs());
  };
})();
