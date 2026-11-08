(() => {
  const key = 'hugo-book.theme';
  const modes = ['auto', 'light', 'dark'];
  const root = document.documentElement;
  let mode = root.dataset.theme;

  try {
    const saved = localStorage.getItem(key);
    if (modes.includes(saved)) mode = saved;
  } catch {}

  function apply() {
    root.dataset.theme = mode;
    document.querySelectorAll('meta[name="theme-color"]').forEach(meta => {
      const dark = mode === 'dark' || (mode === 'auto' && meta.media.includes('dark'));
      meta.content = dark ? '#2e3440' : '#ffffff';
    });
  }

  apply();

  document.addEventListener('DOMContentLoaded', () => {
    const select = document.querySelector('#book-theme-select');
    if (!select) return;

    select.value = mode;
    select.parentElement.hidden = false;
    select.addEventListener('change', () => {
      if (!modes.includes(select.value)) return;
      mode = select.value;
      apply();

      try {
        if (mode === 'auto') localStorage.removeItem(key);
        else localStorage.setItem(key, mode);
      } catch {}
    });
  });
})();
