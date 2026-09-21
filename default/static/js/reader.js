const readerIcons = {
  leftExpand: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6"/><path d="M9 4v16"/><path d="m14 10 2 2-2 2"/></svg>',
  leftCollapse: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6"/><path d="M9 4v16"/><path d="m15 10-2 2 2 2"/></svg>',
  right: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6"/><path d="M15 4v16"/><path d="m9 10 2 2-2 2"/></svg>'
};

function initReaderChrome() {
  const layout = document.querySelector('.layout');
  const left = document.getElementById('toggleReaderLeft');
  const right = document.getElementById('toggleReaderRight');
  if (left) {
    const sync = () => {
      left.innerHTML = layout && layout.classList.contains('reader-left-collapsed')
        ? readerIcons.leftExpand
        : readerIcons.leftCollapse;
    };
    sync();
    left.addEventListener('click', () => {
      if (!layout) return;
      layout.classList.toggle('reader-left-collapsed');
      sync();
    });
  }
  if (right) right.innerHTML = readerIcons.right;
}

initReaderChrome();
