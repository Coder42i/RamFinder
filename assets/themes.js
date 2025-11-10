/* assets/theme.js — robust Light/Dark toggle with icon (🌙 / ☀️) */
(function () {
  const KEY  = 'rf:theme';
  const ROOT = document.documentElement;

  // 1) Apply saved theme ASAP (default: light)
  apply((localStorage.getItem(KEY) || 'light').toLowerCase());

  // 2) Inject button when DOM is ready; retry if header not found yet
  const MAX_TRIES = 40; // ~1s total
  let tries = 0;

  function ensureButton() {
    const header = document.querySelector('header');
    if (!header) {
      if (tries++ < MAX_TRIES) return setTimeout(ensureButton, 25);
      // Fallback: append to body top if no header found
      return attachButton(document.body, 'append');
    }
    // Prefer to insert near Admin link, else before last header child
    const adminLink = document.getElementById('adminLink');
    if (adminLink && adminLink.parentElement === header) {
      attachButton(adminLink, 'before');
    } else {
      attachButton(header, 'append');
    }
  }

  function attachButton(anchor, where) {
    const existing = document.getElementById('themeToggle');
    const cur = ROOT.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    if (existing) return; // already present

    const btn = document.createElement('button');
    btn.id = 'themeToggle';
    btn.type = 'button';
    btn.className = 'btn secondary icon-btn';
    btn.setAttribute('aria-pressed', cur === 'dark' ? 'true' : 'false');
    btn.title = cur === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
    btn.innerHTML = cur === 'dark' ? '☀️' : '🌙';
    btn.addEventListener('click', () => {
      const next = ROOT.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      apply(next);
      btn.setAttribute('aria-pressed', next === 'dark' ? 'true' : 'false');
      btn.title = next === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
      btn.innerHTML = next === 'dark' ? '☀️' : '🌙';
    });

    if (where === 'before' && anchor && anchor.parentElement) {
      anchor.parentElement.insertBefore(btn, anchor);
    } else if (anchor) {
      anchor.appendChild(btn);
    } else {
      document.body.appendChild(btn);
    }
  }

  function apply(theme) {
    const t = theme === 'dark' ? 'dark' : 'light';
    ROOT.setAttribute('data-theme', t);
    localStorage.setItem(KEY, t);
  }

  // Kick off
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensureButton);
  } else {
    ensureButton();
  }
})();
