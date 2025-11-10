/* assets/theme.js — Light/Dark theme toggle (default: light) */
(function () {
  const KEY = 'rf:theme';
  const ROOT = document.documentElement;

  // Default to light if nothing stored
  const initial = (localStorage.getItem(KEY) || 'light').toLowerCase();
  apply(initial);

  // Build a toggle button and inject into every page header
  window.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('header');
    if (!header) return;

    const btn = document.createElement('button');
    btn.id = 'themeToggle';
    btn.className = 'btn secondary';
    btn.type = 'button';
    btn.style.width = 'auto';
    btn.setAttribute('aria-pressed', initial === 'dark' ? 'true' : 'false');
    btn.textContent = initial === 'dark' ? 'Light mode' : 'Dark mode';
    btn.addEventListener('click', () => {
      const next = ROOT.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      apply(next);
      btn.setAttribute('aria-pressed', next === 'dark' ? 'true' : 'false');
      btn.textContent = next === 'dark' ? 'Light mode' : 'Dark mode';
    });

    // Insert before Admin button if present, otherwise at end of header
    const adminLink = document.getElementById('adminLink');
    if (adminLink && adminLink.parentElement === header) {
      header.insertBefore(btn, adminLink);
    } else {
      header.appendChild(btn);
    }
  });

  function apply(theme) {
    const t = (theme === 'dark') ? 'dark' : 'light';
    ROOT.setAttribute('data-theme', t);
    localStorage.setItem(KEY, t);
  }
})();
