/**
 * ACR-QA Demo Mode — ?demo=1
 *
 * When the URL contains ?demo=1, this module:
 *  1. Bypasses the normal auth redirect (uses a read-only DEMO_TOKEN marker in sessionStorage)
 *  2. Fetches /v1/demo/run to get the fixture run_id
 *  3. Injects an amber "DEMO MODE" banner at the top of the page
 *  4. Hides all elements with class .demo-hide (POST/DELETE buttons)
 *
 * Pages opt-in by including: <script src="demo.js"></script>
 * The script runs immediately and sets window.DEMO_MODE / window.DEMO_RUN_ID
 * before the page's own scripts execute (place before page-specific scripts).
 */

(function () {
  'use strict';

  const params = new URLSearchParams(location.search);
  const isDemoMode = params.get('demo') === '1';
  if (!isDemoMode) return;

  // Mark demo mode globally so page scripts can check
  window.DEMO_MODE = true;
  window.DEMO_RUN_ID = null;

  // Store a marker so auth checks don't redirect
  sessionStorage.setItem('acrqa_demo', '1');

  // Override auth check: if page would redirect to login, keep URL but add demo=1
  const _origHref = Object.getOwnPropertyDescriptor(Location.prototype, 'href');
  if (_origHref && _origHref.set) {
    // Patch location.href setter to preserve demo mode on login redirect
    Object.defineProperty(window.location, 'href', {
      set(url) {
        if (String(url).includes('login.html') && sessionStorage.getItem('acrqa_demo') === '1') {
          // Don't redirect to login in demo mode
          return;
        }
        _origHref.set.call(window.location, url);
      },
      get: _origHref.get,
    });
  }

  // Inject demo banner immediately (before DOM ready if possible)
  function injectBanner() {
    if (document.getElementById('demo-banner')) return;
    document.body.classList.add('demo-mode');
    const banner = document.createElement('div');
    banner.id = 'demo-banner';
    banner.className = 'demo-banner';
    banner.innerHTML = `
      <span class="db-dot"></span>
      <span class="db-text">
        <strong>DEMO MODE</strong> — read-only sandbox · viewing a pre-loaded DVPWA scan ·
        <a href="signup.html">Sign up free</a> to scan your own code
      </span>
      <button class="db-close" title="Dismiss" onclick="this.parentElement.remove();document.body.classList.remove('demo-mode')">×</button>
    `;
    document.body.insertBefore(banner, document.body.firstChild);
  }

  if (document.body) {
    injectBanner();
  } else {
    document.addEventListener('DOMContentLoaded', injectBanner);
  }

  // Hide mutation elements
  function hideDemoElements() {
    document.querySelectorAll('.demo-hide').forEach(el => { el.style.display = 'none'; });
  }
  document.addEventListener('DOMContentLoaded', hideDemoElements);

  // Fetch fixture run_id from the public demo endpoint
  fetch('/v1/demo/run')
    .then(r => r.json())
    .then(data => {
      if (data.run_id) {
        window.DEMO_RUN_ID = data.run_id;
        // Dispatch event so page scripts can pick it up
        window.dispatchEvent(new CustomEvent('demo-run-ready', { detail: data }));
      }
    })
    .catch(() => {
      // Demo endpoint unreachable — continue without fixture run
    });
})();
