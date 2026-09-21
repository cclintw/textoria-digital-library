const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let DATA = [];
const searchState = {q: '', rows: [], page: 1, pageSize: 50};

fetch('data/search_index.json').then(r => r.json()).then(d => { DATA = d.paragraphs || []; });

function chars(s) {
  return [...String(s ?? '')];
}

function preview(text, length = 100) {
  const c = chars(text);
  return c.length <= length ? c.join('') : c.slice(0, length).join('');
}

function highlightText(text, q) {
  return esc(text).replaceAll(esc(q), `<mark>${esc(q)}</mark>`);
}

function formatSearchTerms(q) {
  return `<span class="search-term">${esc(q)}</span>`;
}

function updateSearchAssist(q) {
  document.querySelectorAll('.search-assist').forEach(el => el.classList.toggle('is-hidden', Boolean(q)));
}

function runSearch() {
  const q = document.getElementById('q').value.trim();
  updateSearchAssist(q);
  if (!q) {
    document.getElementById('activeSearchTerms').textContent = '';
    document.getElementById('results').innerHTML = '';
    return;
  }
  searchState.q = q;
  searchState.rows = DATA.filter(x => x.text.includes(q));
  searchState.page = 1;
  renderSearchResults();
}

function searchPager(page, totalPages, totalRows, start, count) {
  if (!totalRows) return '';
  const from = start + 1, to = start + count;
  return `<nav class="pager"><span>第 ${from}-${to} 筆（${page} / ${totalPages} 頁）</span><span class="pager-controls"><button type="button" data-search-page="${page - 1}" ${page <= 1 ? 'disabled' : ''}>上一頁</button><button type="button" data-search-page="${page + 1}" ${page >= totalPages ? 'disabled' : ''}>下一頁</button></span></nav>`;
}

function renderSearchResults() {
  const {q, rows, page, pageSize} = searchState;
  document.getElementById('activeSearchTerms').innerHTML = `<span class="term-list">檢索模式：實體擴展　檢索字串：${formatSearchTerms(q)}</span>`;
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
  const start = (page - 1) * pageSize;
  const pageRows = rows.slice(start, start + pageSize);
  const pager = searchPager(page, totalPages, rows.length, start, pageRows.length);
  const head = `<div class="search-result-head"><h3>顯示筆數</h3><div class="search-actions"><button type="button" class="tag-action" data-snippet-action="expand">全部展開</button><button type="button" class="tag-action" data-snippet-action="collapse">全部收合</button></div></div><p class="meta">共找到 <span class="search-term">${rows.length}</span> 筆</p>`;
  document.getElementById('results').innerHTML = head + pager + pageRows.map(r => {
    const shortText = preview(r.text, 100);
    const canToggle = chars(r.text).length > 100;
    return `<div class="result"><a class="result-title" href="${r.href}">${esc(r.division_path)} 第 #${esc(r.paragraph_index || '')} 段</a><div class="snippet" data-full-text="${esc(r.text)}" data-short-text="${esc(shortText)}" data-query="${esc(q)}" data-expanded="false">${highlightText(shortText, q)}${canToggle ? '...<button type="button" class="snippet-toggle">顯示全部</button>' : ''}</div></div>`;
  }).join('') + pager;
}

function setAllSearchSnippets(expanded) {
  document.querySelectorAll('#results .snippet[data-full-text]').forEach(snippet => {
    const text = expanded ? snippet.dataset.fullText : snippet.dataset.shortText;
    const canToggle = snippet.dataset.fullText !== snippet.dataset.shortText;
    snippet.dataset.expanded = expanded ? 'true' : 'false';
    snippet.innerHTML = `${highlightText(text, snippet.dataset.query)}${canToggle ? (expanded ? ' <button type="button" class="snippet-toggle">收合</button>' : '...<button type="button" class="snippet-toggle">顯示全部</button>') : ''}`;
  });
}

document.getElementById('q').addEventListener('input', runSearch);
document.querySelectorAll('[data-search-example]').forEach(btn => btn.addEventListener('click', () => {
  document.getElementById('q').value = btn.dataset.searchExample;
  runSearch();
}));

document.addEventListener('click', e => {
  const pageButton = e.target.closest('[data-search-page]');
  if (pageButton) {
    e.preventDefault();
    const max = Math.max(1, Math.ceil(searchState.rows.length / searchState.pageSize));
    searchState.page = Math.min(max, Math.max(1, Number(pageButton.dataset.searchPage)));
    renderSearchResults();
    return;
  }
  const action = e.target.closest('[data-snippet-action]');
  if (action) {
    e.preventDefault();
    setAllSearchSnippets(action.dataset.snippetAction === 'expand');
    return;
  }
  const toggle = e.target.closest('.snippet-toggle');
  if (toggle) {
    const snippet = toggle.closest('.snippet');
    const expanded = snippet.dataset.expanded === 'true';
    const text = expanded ? snippet.dataset.shortText : snippet.dataset.fullText;
    snippet.dataset.expanded = expanded ? 'false' : 'true';
    snippet.innerHTML = expanded
      ? `${highlightText(text, snippet.dataset.query)}...<button type="button" class="snippet-toggle">顯示全部</button>`
      : `${highlightText(text, snippet.dataset.query)} <button type="button" class="snippet-toggle">收合</button>`;
  }
});
