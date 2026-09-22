const readerIcons = {
  leftExpand: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6"/><path d="M9 4v16"/><path d="m14 10 2 2-2 2"/></svg>',
  leftCollapse: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6"/><path d="M9 4v16"/><path d="m15 10-2 2 2 2"/></svg>',
  right: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6"/><path d="M15 4v16"/><path d="m9 10 2 2-2 2"/></svg>'
};

function initReaderChrome() {
  const layout = document.querySelector('.layout');
  const left = document.getElementById('toggleReaderLeft');
  const right = document.getElementById('toggleReaderRight');
  const mobileQuery = window.matchMedia('(max-width: 910px)');
  const storageKey = 'textoria.readerLeftCollapsed.session';
  const readDesktopPreference = () => {
    try {
      return window.sessionStorage.getItem(storageKey);
    } catch {
      return null;
    }
  };
  const writeDesktopPreference = collapsed => {
    try {
      window.sessionStorage.setItem(storageKey, collapsed ? 'true' : 'false');
    } catch {
      /* Ignore unavailable storage. */
    }
  };
  if (left) {
    const sync = () => {
      left.innerHTML = layout && layout.classList.contains('reader-left-collapsed')
        ? readerIcons.leftExpand
        : readerIcons.leftCollapse;
    };
    if (layout) {
      const desktopPreference = readDesktopPreference();
      if (mobileQuery.matches || desktopPreference !== 'false') {
        layout.classList.add('reader-left-collapsed');
      } else {
        layout.classList.remove('reader-left-collapsed');
      }
    }
    sync();
    left.addEventListener('click', () => {
      if (!layout) return;
      layout.classList.toggle('reader-left-collapsed');
      if (!mobileQuery.matches) {
        writeDesktopPreference(layout.classList.contains('reader-left-collapsed'));
      }
      sync();
    });
  }
  if (right) right.innerHTML = readerIcons.right;
  document.querySelectorAll('.toc-link').forEach(link => {
    link.addEventListener('click', () => {
      if (!layout || !mobileQuery.matches) return;
      layout.classList.add('reader-left-collapsed');
      sync();
    });
  });
}

function initTocTree() {
  document.querySelectorAll('.toc-toggle').forEach(button => {
    const item = button.closest('.toc-item');
    const children = item ? item.querySelector(':scope > .toc-children') : null;
    if (!children) return;
    const setExpanded = expanded => {
      button.setAttribute('aria-expanded', expanded ? 'true' : 'false');
      button.textContent = expanded ? '▾' : '▸';
      children.hidden = !expanded;
    };
    setExpanded(button.getAttribute('aria-expanded') === 'true');
    button.addEventListener('click', () => {
      setExpanded(button.getAttribute('aria-expanded') !== 'true');
    });
  });
}

function initReaderPageEnter() {
  const content = document.getElementById('readerContent');
  const layout = document.querySelector('.layout');
  if (!content) return;
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      if (layout) layout.classList.remove('reader-entering');
      content.classList.add('reader-slide-active');
    });
  });
}

initReaderChrome();
initTocTree();
initReaderPageEnter();
