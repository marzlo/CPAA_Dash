import json
from datetime import datetime

with open("dashboard_data.json", encoding="utf-8") as f:
    DATA = json.load(f)

DATA_JSON = json.dumps(DATA, ensure_ascii=False)
UPDATED_AT = datetime.now().strftime("%Y-%m-%d")

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CPAA SWE3 / SWE5 Dashboard</title>
<style>
  :root {
    color-scheme: light;
    --surface-1: #fcfcfb;
    --page: #f9f9f7;
    --text-primary: #0b0b0b;
    --text-secondary: #52514e;
    --muted: #898781;
    --grid: #e1e0d9;
    --baseline: #c3c2b7;
    --border: rgba(11,11,11,0.10);
    --series-cp: #2a78d6;
    --series-aa: #eb6834;
    --series-ipod: #1baf7a;
    --good: #0ca30c;
    --warning: #fab219;
    --serious: #ec835a;
    --critical: #d03b3b;
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) {
      color-scheme: dark;
      --surface-1: #1a1a19;
      --page: #0d0d0d;
      --text-primary: #ffffff;
      --text-secondary: #c3c2b7;
      --muted: #898781;
      --grid: #2c2c2a;
      --baseline: #383835;
      --border: rgba(255,255,255,0.10);
      --series-cp: #3987e5;
      --series-aa: #d95926;
      --series-ipod: #199e70;
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --surface-1: #1a1a19;
    --page: #0d0d0d;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --muted: #898781;
    --grid: #2c2c2a;
    --baseline: #383835;
    --border: rgba(255,255,255,0.10);
    --series-cp: #3987e5;
    --series-aa: #d95926;
    --series-ipod: #199e70;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    background: var(--page);
    color: var(--text-primary);
  }
  header {
    padding: 20px 28px 8px;
  }
  header h1 { margin: 0 0 4px; font-size: 22px; }
  header p { margin: 0; color: var(--text-secondary); font-size: 13px; }
  .theme-toggle {
    position: absolute; top: 20px; right: 28px;
    background: var(--surface-1); border: 1px solid var(--border);
    border-radius: 8px; padding: 6px 12px; cursor: pointer; color: var(--text-primary);
    font-size: 13px;
  }
  nav.tabs {
    display: flex; gap: 8px; padding: 4px 28px 16px; flex-wrap: wrap;
    border-bottom: 1px solid var(--grid);
  }
  nav.tabs button {
    background: transparent; border: none; padding: 8px 16px;
    border-radius: 8px 8px 0 0; cursor: pointer; font-size: 14px;
    color: var(--text-secondary); font-weight: 500;
  }
  nav.tabs button.active {
    background: var(--surface-1); color: var(--text-primary);
    box-shadow: inset 0 -2px 0 var(--series-cp);
  }
  main { padding: 20px 28px 60px; max-width: 1200px; margin: 0 auto; }
  .panel { display: none; }
  .panel.active { display: block; }
  .stat-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }
  .stat-tile {
    background: var(--surface-1); border: 1px solid var(--border);
    border-radius: 10px; padding: 16px 20px; flex: 1; min-width: 190px;
  }
  .stat-tile .label { font-size: 12px; color: var(--muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: .04em; }
  .stat-tile .value { font-size: 30px; font-weight: 700; font-variant-numeric: proportional-nums; }
  .stat-tile .sub { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
  .meter { height: 8px; border-radius: 4px; background: var(--grid); margin-top: 10px; overflow: hidden; }
  .meter > div { height: 100%; background: var(--good); }
  section.card {
    background: var(--surface-1); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px; margin-bottom: 24px;
  }
  section.card h2 { margin: 0 0 4px; font-size: 16px; }
  section.card .caption { color: var(--text-secondary); font-size: 12px; margin-bottom: 16px; }
  .bar-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
  .bar-row .name { width: 90px; font-size: 13px; color: var(--text-secondary); flex-shrink: 0; }
  .bar-row .name.wide { width: 230px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .bar-row .name.assignee { width: 130px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .bar-row-pct { justify-content: flex-start; }
  .pct-value { width: 48px; font-size: 14px; font-weight: 700; font-variant-numeric: tabular-nums; text-align: right; }
  .bar-row-clickable { cursor: pointer; border-radius: 6px; padding: 4px 6px; margin-left: -6px; margin-right: -6px; }
  .bar-row-clickable:hover { background: var(--page); }
  .stat-tile-clickable { cursor: pointer; transition: border-color .15s; }
  .stat-tile-clickable:hover { border-color: var(--series-cp); }
  .bar-track { flex: 1; background: var(--grid); border-radius: 4px; height: 22px; position: relative; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 4px; display: flex; align-items: center; }
  .bar-fill span { font-size: 12px; color: white; padding-left: 8px; font-weight: 600; white-space: nowrap; }
  .bar-count { width: 46px; text-align: right; font-size: 13px; font-variant-numeric: tabular-nums; color: var(--text-primary); }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--grid); }
  th { color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .03em; }
  th[data-sort] { cursor: pointer; user-select: none; white-space: nowrap; }
  th[data-sort]:hover { color: var(--text-primary); }
  th[data-sort]::after { content: ''; display: inline-block; width: 10px; }
  th[data-sort].sort-asc::after { content: '▲'; font-size: 9px; }
  th[data-sort].sort-desc::after { content: '▼'; font-size: 9px; }
  td.key a { color: var(--series-cp); text-decoration: none; }
  td.key a:hover { text-decoration: underline; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
  .badge.done { background: color-mix(in srgb, var(--good) 18%, transparent); color: var(--good); }
  .badge.progress { background: color-mix(in srgb, var(--warning) 22%, transparent); color: #8a6200; }
  .badge.todo { background: color-mix(in srgb, var(--critical) 15%, transparent); color: var(--critical); }
  :root[data-theme="dark"] .badge.progress, @media (prefers-color-scheme: dark) { }
  .filters { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
  .filters select, .filters input {
    background: var(--page); border: 1px solid var(--border); border-radius: 6px;
    padding: 6px 10px; font-size: 13px; color: var(--text-primary);
  }
  .table-wrap { max-height: 480px; overflow: auto; }
  .empty-state { color: var(--muted); font-size: 13px; padding: 20px; text-align: center; }
  .feature-mini { display: flex; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
  .feature-mini .stat-tile { flex: 1; min-width: 160px; }
  .chip-row { display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }
  .chip {
    background: var(--page); border: 1px solid var(--border); border-radius: 999px;
    padding: 5px 12px; font-size: 12px; color: var(--text-secondary); cursor: pointer;
  }
  .chip.active { background: var(--series-cp); border-color: var(--series-cp); color: #fff; }
  .group-header {
    padding: 8px 10px; font-size: 12px; font-weight: 700; color: var(--text-secondary);
    background: var(--page); border-bottom: 1px solid var(--grid);
  }
</style>
</head>
<body>
<button class="theme-toggle" id="themeToggle">🌓 Theme</button>
<header>
  <h1>CPAA SWE3 / SWE5 Ticket Dashboard</h1>
  <p>Mobile Drive · Jira project NR1LT · filter 12399 · 資料來源：使用者匯出的 Jira Excel (CPAA_general_ticket)，共 __TOTAL__ 張 SWE3/SWE5 票、__BUGTOTAL__ 張 Bug 票</p>
  <p style="margin-top:4px; font-weight:600;">最後更新日期：__UPDATED_AT__</p>
</header>
<nav class="tabs" id="tabs">
  <button data-tab="overview" class="active">Overview</button>
  <button data-tab="Bug">Bug</button>
  <button data-tab="Audio">Audio</button>
  <button data-tab="Pretest">Pretest</button>
</nav>
<main>

  <div class="panel active" id="panel-overview">
    <div class="stat-row" id="completionTiles"></div>

    <section class="card">
      <h2>Sub-feature 分佈(僅未完成票,SWE2+SWE3+SWE5 合併計算,依 CarPlay/Android Auto/iPod 分欄)</h2>
      <div style="display:flex; gap:24px; flex-wrap:wrap;">
        <div style="flex:1; min-width:280px;">
          <h3 style="margin:0 0 4px; font-size:14px;">CarPlay</h3>
          <p class="caption" id="subFeatureBarsCaption-CarPlay"></p>
          <div id="subFeatureBars-CarPlay"></div>
        </div>
        <div style="flex:1; min-width:280px;">
          <h3 style="margin:0 0 4px; font-size:14px;">Android Auto</h3>
          <p class="caption" id="subFeatureBarsCaption-AndroidAuto"></p>
          <div id="subFeatureBars-AndroidAuto"></div>
        </div>
        <div style="flex:1; min-width:280px;">
          <h3 style="margin:0 0 4px; font-size:14px;">iPod</h3>
          <p class="caption" id="subFeatureBarsCaption-iPod"></p>
          <div id="subFeatureBars-iPod"></div>
        </div>
      </div>
    </section>

    <section class="card">
      <h2>Assignee 分佈(僅未完成票,SWE2+SWE3+SWE5 合併計算,依組織分欄)</h2>
      <p class="caption">組織對應依據 cpaa-dashboard skill 的 TEAM_MAP;沒有對應到組織的人歸在「Unknown」</p>
      <div id="assigneeBarsContainer" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:24px;"></div>
    </section>

    <section class="card">
      <h2>票清單(依 Label 分類篩選)</h2>
      <p class="caption" id="missingCaption"></p>
      <div class="filters">
        <select id="missingSweFilter">
          <option value="">全部 SWE</option>
          <option value="SWE2">SWE2</option>
          <option value="SWE3">SWE3</option>
          <option value="SWE5">SWE5</option>
        </select>
        <select id="missingFeatureFilter">
          <option value="">全部 Feature</option>
          <option value="CarPlay">CarPlay</option>
          <option value="Android Auto">Android Auto</option>
          <option value="iPod">iPod</option>
        </select>
        <select id="missingStatusFilter">
          <option value="">全部狀態</option>
          <option value="done">已完成</option>
          <option value="not-done">未完成</option>
        </select>
        <select id="missingLabelFilter">
          <option value="">全部 Label 分類</option>
          <option value="ASW-R2">ASW-R2</option>
          <option value="ASW-R3 (不含CPAA 0830)">ASW-R3 (不含CPAA 0830)</option>
          <option value="CPAA0830">CPAA0830</option>
          <option value="三者皆無" selected>三者皆無</option>
        </select>
        <select id="missingSubFeatureFilter">
          <option value="">全部 Sub-feature</option>
        </select>
        <select id="missingAssigneeFilter">
          <option value="">全部 Assignee</option>
        </select>
        <input type="text" id="missingSearch" placeholder="搜尋 key 或 summary...">
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th data-sort="key">Key</th><th data-sort="swe">SWE</th><th data-sort="feature">Feature</th>
            <th data-sort="subFeature">Sub-feature</th><th data-sort="assignee">Assignee</th>
            <th data-sort="status">Status</th><th data-sort="labelBucket">Label 分類</th><th data-sort="summary">Summary</th>
          </tr></thead>
          <tbody id="missingTbody"></tbody>
        </table>
      </div>
    </section>
  </div>

  <div class="panel" id="panel-Bug"></div>
  <div class="panel" id="panel-Audio"></div>
  <div class="panel" id="panel-Pretest"></div>

</main>

<script>
const RAW = __DATA_JSON__;
const DATA = RAW.tickets;
const BUGS = RAW.bugs;
const AUDIO = RAW.audio;
const PRETEST = RAW.pretest;
const FEATURE_COLORS = { "CarPlay": "var(--series-cp)", "Android Auto": "var(--series-aa)", "iPod": "var(--series-ipod)" };

function esc(s) {
  return (s || "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
}
function statusBadge(rec) {
  if (rec.done) return '<span class="badge done">Done</span>';
  if (rec.statusCategory === 'indeterminate') return '<span class="badge progress">' + esc(rec.status) + '</span>';
  return '<span class="badge todo">' + esc(rec.status) + '</span>';
}
function bugStatusBadge(rec) {
  // Unlike statusBadge, always show the real Jira status text (e.g. "Eng build", "Ready for test",
  // "Monitoring") even for tickets counted as done, instead of collapsing them to a generic "Done" label.
  if (rec.done) return '<span class="badge done">' + esc(rec.status) + '</span>';
  if (rec.statusCategory === 'indeterminate') return '<span class="badge progress">' + esc(rec.status) + '</span>';
  return '<span class="badge todo">' + esc(rec.status) + '</span>';
}
function ticketUrl(key) { return "https://mobiledrivetech.atlassian.net/browse/" + key; }

function jumpToSwe(swe) {
  document.getElementById('missingSweFilter').value = swe || '';
  document.getElementById('missingFeatureFilter').value = '';
  document.getElementById('missingStatusFilter').value = 'not-done';
  document.getElementById('missingSubFeatureFilter').value = '';
  document.getElementById('missingLabelFilter').value = '';
  document.getElementById('missingAssigneeFilter').value = '';
  document.getElementById('missingSearch').value = '';
  renderMissingTable();
  document.getElementById('missingTbody').closest('section.card').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderCompletion() {
  const el = document.getElementById('completionTiles');
  ['SWE2', 'SWE3', 'SWE5'].forEach(swe => {
    const subset = DATA.filter(r => r.swe === swe);
    const done = subset.filter(r => r.done).length;
    const total = subset.length;
    const notDone = total - done;
    const pct = total ? Math.round(done / total * 100) : 0;
    const tile = document.createElement('div');
    tile.className = 'stat-tile stat-tile-clickable';
    tile.innerHTML = `
      <div class="label">${swe} 完成率</div>
      <div class="value">${notDone}</div>
      <div class="sub">未完成 · 完成率 ${pct}%(${done} / ${total} 已完成)</div>
      <div class="meter"><div style="width:${pct}%"></div></div>
    `;
    tile.addEventListener('click', () => jumpToSwe(swe));
    el.appendChild(tile);
  });
  const totalDone = DATA.filter(r => r.done).length;
  const totalNotDone = DATA.length - totalDone;
  const totalPct = DATA.length ? Math.round(totalDone / DATA.length * 100) : 0;
  const tile = document.createElement('div');
  tile.className = 'stat-tile stat-tile-clickable';
  tile.innerHTML = `
    <div class="label">合計 (SWE2+SWE3+SWE5)</div>
    <div class="value">${totalNotDone}</div>
    <div class="sub">未完成 · 完成率 ${totalPct}%(${totalDone} / ${DATA.length} 已完成)</div>
    <div class="meter"><div style="width:${totalPct}%"></div></div>
  `;
  tile.addEventListener('click', () => jumpToSwe(''));
  el.appendChild(tile);
}

const LABEL_BUCKETS = ['ASW-R2', 'ASW-R3 (不含CPAA 0830)', 'CPAA0830', '三者皆無'];
const LABEL_BUCKET_COLORS = {
  'ASW-R2': 'var(--series-cp)',
  'ASW-R3 (不含CPAA 0830)': 'var(--series-ipod)',
  'CPAA0830': 'var(--warning)',
  '三者皆無': 'var(--muted)',
};

function renderLabelBarsFor(swe) {
  const el = document.getElementById('labelBars-' + swe);
  const notDone = DATA.filter(r => !r.done && r.swe === swe);
  const total = notDone.length;
  document.getElementById('labelBarsCaption-' + swe).textContent =
    `在 ${total} 張未完成的 ${swe} 票中,依標籤分類的票數(每張票只計入一類,依 ASW-R2 → ASW-R3(不含CPAA 0830) → CPAA0830 → 三者皆無 的優先順序判斷)`;
  const rows = LABEL_BUCKETS.map(name => ({
    name,
    count: notDone.filter(r => r.labelBucket === name).length,
    color: LABEL_BUCKET_COLORS[name],
  }));
  rows.forEach(row => {
    const pct = total ? Math.round(row.count / total * 100) : 0;
    const div = document.createElement('div');
    div.className = 'bar-row';
    div.innerHTML = `
      <div class="name">${row.name}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.max(pct,3)}%; background:${row.color}"><span>${pct}%</span></div></div>
      <div class="bar-count">${row.count}</div>
    `;
    el.appendChild(div);
  });
}
function renderLabelBars() {
  renderLabelBarsFor('SWE3');
  renderLabelBarsFor('SWE5');
}

const SUBFEATURE_GROUPS = [
  { feature: 'CarPlay', elId: 'CarPlay', color: 'var(--series-cp)' },
  { feature: 'Android Auto', elId: 'AndroidAuto', color: 'var(--series-aa)' },
  { feature: 'iPod', elId: 'iPod', color: 'var(--series-ipod)' },
];

function stripGroupPrefix(name) {
  if (name === '未分類') return name;
  const idx = name.indexOf('_');
  return idx === -1 ? name : name.slice(idx + 1);
}

const sortCollator = new Intl.Collator('zh-Hant', { numeric: true, sensitivity: 'base' });
function sortRows(rows, key, dir) {
  if (!key) return rows;
  const sorted = rows.slice().sort((a, b) => {
    let va = a[key], vb = b[key];
    if (typeof va === 'boolean' || typeof vb === 'boolean') {
      va = va ? 1 : 0;
      vb = vb ? 1 : 0;
      return va - vb;
    }
    if (va === null || va === undefined) va = '';
    if (vb === null || vb === undefined) vb = '';
    if (typeof va === 'number' && typeof vb === 'number') return va - vb;
    return sortCollator.compare(String(va), String(vb));
  });
  return dir === 'desc' ? sorted.reverse() : sorted;
}

function attachSortHandlers(theadEl, sortState, renderFn) {
  const ths = theadEl.querySelectorAll('th[data-sort]');
  ths.forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.sort;
      if (sortState.key === key) {
        sortState.dir = sortState.dir === 'asc' ? 'desc' : 'asc';
      } else {
        sortState.key = key;
        sortState.dir = 'asc';
      }
      ths.forEach(t => t.classList.remove('sort-asc', 'sort-desc'));
      th.classList.add(sortState.dir === 'asc' ? 'sort-asc' : 'sort-desc');
      renderFn();
    });
  });
}

function renderSubFeatureBarsFor(group) {
  const el = document.getElementById('subFeatureBars-' + group.elId);
  const notDone = DATA.filter(r => !r.done && r.feature === group.feature);
  const total = notDone.length;
  document.getElementById('subFeatureBarsCaption-' + group.elId).textContent =
    `在 ${total} 張未完成的 ${group.feature} 票中(SWE2+SWE3+SWE5 合併),依功能子分類(cpaa-feature-taxonomy)統計的票數;無法明確對應到子分類的票歸在「未分類」`;
  const counts = {};
  notDone.forEach(r => { counts[r.subFeature] = (counts[r.subFeature] || 0) + 1; });
  const rows = Object.keys(counts)
    .map(name => ({ name: stripGroupPrefix(name), fullName: name, count: counts[name] }))
    .sort((a, b) => b.count - a.count);
  el.innerHTML = '';
  rows.forEach(row => {
    const pct = total ? Math.round(row.count / total * 100) : 0;
    const color = row.fullName === '未分類' ? 'var(--muted)' : group.color;
    const div = document.createElement('div');
    div.className = 'bar-row bar-row-pct bar-row-clickable';
    div.title = `點擊查看「${row.name}」的票`;
    div.innerHTML = `
      <div class="name wide" title="${row.name}">${row.name}</div>
      <div class="pct-value" style="color:${color}">${pct}%</div>
      <div class="bar-count">${row.count}</div>
    `;
    div.addEventListener('click', () => jumpToSubFeature(group.feature, row.fullName));
    el.appendChild(div);
  });
}

function jumpToSubFeature(feature, fullSubFeature) {
  document.getElementById('missingFeatureFilter').value = feature;
  document.getElementById('missingSubFeatureFilter').value = fullSubFeature;
  document.getElementById('missingStatusFilter').value = 'not-done';
  document.getElementById('missingLabelFilter').value = '';
  document.getElementById('missingSweFilter').value = '';
  document.getElementById('missingAssigneeFilter').value = '';
  document.getElementById('missingSearch').value = '';
  renderMissingTable();
  document.getElementById('missingTbody').closest('section.card').scrollIntoView({ behavior: 'smooth', block: 'start' });
}
function renderSubFeatureBars() {
  SUBFEATURE_GROUPS.forEach(renderSubFeatureBarsFor);
}

const TEAM_ORDER = ['TS_FW', 'TS_CPAA', 'MDT_System', 'MDT_PM', 'MDT_App', 'MDI_System', 'Unassigned', 'Unknown'];
const SEVERITY_ORDER = ['Critical', 'Serious', 'Moderate', 'Minor', '未標示'];
const PRIORITY_ORDER = ['Critical', 'Highest', 'High', 'Medium', 'Low', 'Lowest', '未標示'];
const missingSortState = { key: '', dir: 'asc' };

function jumpToAssignee(assignee) {
  document.getElementById('missingAssigneeFilter').value = assignee;
  document.getElementById('missingFeatureFilter').value = '';
  document.getElementById('missingStatusFilter').value = 'not-done';
  document.getElementById('missingSubFeatureFilter').value = '';
  document.getElementById('missingLabelFilter').value = '';
  document.getElementById('missingSweFilter').value = '';
  document.getElementById('missingSearch').value = '';
  renderMissingTable();
  document.getElementById('missingTbody').closest('section.card').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderAssigneeBars() {
  const container = document.getElementById('assigneeBarsContainer');
  container.innerHTML = '';
  const notDone = DATA.filter(r => !r.done);
  const teamsPresent = TEAM_ORDER.filter(team => notDone.some(r => r.team === team));
  teamsPresent.forEach(team => {
    const teamRows = notDone.filter(r => r.team === team);
    const total = teamRows.length;
    const counts = {};
    teamRows.forEach(r => { counts[r.assignee] = (counts[r.assignee] || 0) + 1; });
    const rows = Object.keys(counts)
      .map(name => ({ name, count: counts[name] }))
      .sort((a, b) => b.count - a.count);

    const col = document.createElement('div');
    col.style.cssText = 'flex:1 1 260px; min-width:260px; max-width:100%; overflow:hidden;';
    col.innerHTML = `
      <h3 style="margin:0 0 4px; font-size:14px;">${esc(team)}</h3>
      <p class="caption">在 ${total} 張未完成票中,依 assignee 統計的票數</p>
      <div class="bars-target"></div>
    `;
    const target = col.querySelector('.bars-target');
    rows.forEach(row => {
      const pct = total ? Math.round(row.count / total * 100) : 0;
      const div = document.createElement('div');
      div.className = 'bar-row bar-row-pct bar-row-clickable';
      div.title = `點擊查看 ${row.name} 的票`;
      div.innerHTML = `
        <div class="name assignee" title="${esc(row.name)}">${esc(row.name)}</div>
        <div class="pct-value" style="color:var(--series-cp)">${pct}%</div>
        <div class="bar-count">${row.count}</div>
      `;
      div.addEventListener('click', () => jumpToAssignee(row.name));
      target.appendChild(div);
    });
    container.appendChild(col);
  });
}

function populateMissingSubFeatureFilter() {
  const sel = document.getElementById('missingSubFeatureFilter');
  const byFeature = {};
  DATA.forEach(r => {
    if (r.subFeature === '未分類') return;
    (byFeature[r.feature] = byFeature[r.feature] || new Set()).add(r.subFeature);
  });
  ['CarPlay', 'Android Auto', 'iPod'].forEach(feature => {
    const names = byFeature[feature];
    if (!names || !names.size) return;
    const optgroup = document.createElement('optgroup');
    optgroup.label = feature;
    Array.from(names).sort().forEach(full => {
      const opt = document.createElement('option');
      opt.value = full;
      opt.textContent = stripGroupPrefix(full);
      optgroup.appendChild(opt);
    });
    sel.appendChild(optgroup);
  });
  const uncatOpt = document.createElement('option');
  uncatOpt.value = '未分類';
  uncatOpt.textContent = '未分類';
  sel.appendChild(uncatOpt);
}

function populateMissingAssigneeFilter() {
  const sel = document.getElementById('missingAssigneeFilter');
  const names = Array.from(new Set(DATA.map(r => r.assignee))).sort();
  names.forEach(name => {
    const opt = document.createElement('option');
    opt.value = name;
    opt.textContent = name;
    sel.appendChild(opt);
  });
}

function renderMissingTable() {
  const sweFilter = document.getElementById('missingSweFilter').value;
  const featureFilter = document.getElementById('missingFeatureFilter').value;
  const statusFilter = document.getElementById('missingStatusFilter').value;
  const labelFilter = document.getElementById('missingLabelFilter').value;
  const subFeatureFilter = document.getElementById('missingSubFeatureFilter').value;
  const assigneeFilter = document.getElementById('missingAssigneeFilter').value;
  const search = document.getElementById('missingSearch').value.toLowerCase();
  const tbody = document.getElementById('missingTbody');
  let rows = DATA;
  if (statusFilter === 'done') rows = rows.filter(r => r.done);
  if (statusFilter === 'not-done') rows = rows.filter(r => !r.done);
  if (labelFilter) rows = rows.filter(r => r.labelBucket === labelFilter);
  if (sweFilter) rows = rows.filter(r => r.swe === sweFilter);
  if (featureFilter) rows = rows.filter(r => r.feature === featureFilter);
  if (subFeatureFilter) rows = rows.filter(r => r.subFeature === subFeatureFilter);
  if (assigneeFilter) rows = rows.filter(r => r.assignee === assigneeFilter);
  if (search) rows = rows.filter(r => r.key.toLowerCase().includes(search) || r.summary.toLowerCase().includes(search));
  rows = sortRows(rows, missingSortState.key, missingSortState.dir);
  document.getElementById('missingCaption').textContent = `共 ${rows.length} 張票 (DATA 總數 ${DATA.length} 張,含已完成與未完成)`;
  tbody.innerHTML = rows.length ? rows.map(r => `
    <tr>
      <td class="key"><a href="${ticketUrl(r.key)}" target="_blank">${r.key}</a></td>
      <td>${r.swe}</td>
      <td>${esc(r.feature)}</td>
      <td>${esc(stripGroupPrefix(r.subFeature))}</td>
      <td>${esc(r.assignee)}</td>
      <td>${statusBadge(r)}</td>
      <td>${esc(r.labelBucket)}</td>
      <td>${esc(r.summary)}</td>
    </tr>
  `).join('') : '<tr><td colspan="8" class="empty-state">沒有符合條件的票</td></tr>';
}

function renderBugPanel() {
  const panel = document.getElementById('panel-Bug');
  const done = BUGS.filter(r => r.done).length;
  const total = BUGS.length;
  const pct = total ? Math.round(done / total * 100) : 0;
  panel.innerHTML = `
    <div class="stat-row" id="bugSeverityTiles"></div>
    <div class="stat-row" id="bugPriorityTiles"></div>
    <section class="card">
      <h2>Label 分佈(僅未完成 Bug)</h2>
      <p class="caption" id="bugLabelBarsCaption"></p>
      <div id="bugLabelBars"></div>
    </section>
    <section class="card">
      <h2>Sub-feature 分佈(僅未完成 Bug,依 CarPlay/Android Auto/iPod 分欄)</h2>
      <div style="display:flex; gap:24px; flex-wrap:wrap;">
        <div style="flex:1; min-width:280px;">
          <h3 style="margin:0 0 4px; font-size:14px;">CarPlay</h3>
          <p class="caption" id="bugSubFeatureBarsCaption-CarPlay"></p>
          <div id="bugSubFeatureBars-CarPlay"></div>
        </div>
        <div style="flex:1; min-width:280px;">
          <h3 style="margin:0 0 4px; font-size:14px;">Android Auto</h3>
          <p class="caption" id="bugSubFeatureBarsCaption-AndroidAuto"></p>
          <div id="bugSubFeatureBars-AndroidAuto"></div>
        </div>
        <div style="flex:1; min-width:280px;">
          <h3 style="margin:0 0 4px; font-size:14px;">iPod</h3>
          <p class="caption" id="bugSubFeatureBarsCaption-iPod"></p>
          <div id="bugSubFeatureBars-iPod"></div>
        </div>
      </div>
    </section>
    <section class="card">
      <h2>Assignee 分佈(僅未完成 Bug,依組織分欄)</h2>
      <p class="caption">組織對應依據 cpaa-dashboard skill 的 TEAM_MAP;沒有對應到組織的人歸在「Unknown」</p>
      <div id="bugAssigneeBarsContainer" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:24px;"></div>
    </section>
    <section class="card">
      <h2>Bug 清單(依 Feature / Label 分類篩選)</h2>
      <p class="caption" id="bugMissingCaption"></p>
      <div class="filters">
        <select id="bugFeatureFilter">
          <option value="">全部 Feature</option>
          <option value="CarPlay">CarPlay</option>
          <option value="Android Auto">Android Auto</option>
          <option value="iPod">iPod</option>
        </select>
        <select id="bugStatusFilter">
          <option value="">全部狀態</option>
          <option value="done">已完成</option>
          <option value="not-done">未完成</option>
        </select>
        <select id="bugLabelFilter">
          <option value="">全部 Label 分類</option>
          <option value="ASW-R2">ASW-R2</option>
          <option value="ASW-R3 (不含CPAA 0830)">ASW-R3 (不含CPAA 0830)</option>
          <option value="CPAA0830">CPAA0830</option>
          <option value="三者皆無">三者皆無</option>
        </select>
        <select id="bugSubFeatureFilter">
          <option value="">全部 Sub-feature</option>
        </select>
        <select id="bugAssigneeFilter">
          <option value="">全部 Assignee</option>
        </select>
        <select id="bugSeverityFilter">
          <option value="">全部 Severity</option>
        </select>
        <select id="bugPriorityFilter">
          <option value="">全部 Priority</option>
        </select>
        <input type="text" id="bugSearch" placeholder="搜尋 key 或 summary...">
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th data-sort="key">Key</th><th data-sort="feature">Feature</th><th data-sort="subFeature">Sub-feature</th>
            <th data-sort="assignee">Assignee</th><th data-sort="severity">Severity</th><th data-sort="priority">Priority</th><th data-sort="status">Status</th>
            <th data-sort="labelBucket">Label 分類</th><th data-sort="summary">Summary</th>
          </tr></thead>
          <tbody id="bugTbody"></tbody>
        </table>
      </div>
    </section>
  `;

  function renderBugLabelBars() {
    const el = document.getElementById('bugLabelBars');
    el.innerHTML = '';
    const notDone = BUGS.filter(r => !r.done);
    const t = notDone.length;
    document.getElementById('bugLabelBarsCaption').textContent =
      `在 ${t} 張未完成的 Bug 票中,依標籤分類的票數(每張票只計入一類,依 ASW-R2 → ASW-R3(不含CPAA 0830) → CPAA0830 → 三者皆無 的優先順序判斷)`;
    LABEL_BUCKETS.map(name => ({
      name,
      count: notDone.filter(r => r.labelBucket === name).length,
      color: LABEL_BUCKET_COLORS[name],
    })).forEach(row => {
      const pct2 = t ? Math.round(row.count / t * 100) : 0;
      const div = document.createElement('div');
      div.className = 'bar-row';
      div.innerHTML = `
        <div class="name">${row.name}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${Math.max(pct2,3)}%; background:${row.color}"><span>${pct2}%</span></div></div>
        <div class="bar-count">${row.count}</div>
      `;
      el.appendChild(div);
    });
  }
  renderBugLabelBars();

  const featureSel = document.getElementById('bugFeatureFilter');
  const statusSel = document.getElementById('bugStatusFilter');
  const labelSel = document.getElementById('bugLabelFilter');
  const subFeatureSel = document.getElementById('bugSubFeatureFilter');
  const assigneeSel = document.getElementById('bugAssigneeFilter');
  const severitySel = document.getElementById('bugSeverityFilter');
  const prioritySel = document.getElementById('bugPriorityFilter');
  const search = document.getElementById('bugSearch');
  const tbody = document.getElementById('bugTbody');

  Array.from(new Set(BUGS.map(r => r.assignee))).sort().forEach(name => {
    const opt = document.createElement('option');
    opt.value = name;
    opt.textContent = name;
    assigneeSel.appendChild(opt);
  });

  SEVERITY_ORDER.filter(s => BUGS.some(r => r.severity === s)).forEach(name => {
    const opt = document.createElement('option');
    opt.value = name;
    opt.textContent = name;
    severitySel.appendChild(opt);
  });

  PRIORITY_ORDER.filter(p => BUGS.some(r => r.priority === p)).forEach(name => {
    const opt = document.createElement('option');
    opt.value = name;
    opt.textContent = name;
    prioritySel.appendChild(opt);
  });

  (function populateBugSubFeatureFilter() {
    const byFeature = {};
    BUGS.forEach(r => {
      if (r.subFeature === '未分類') return;
      (byFeature[r.feature] = byFeature[r.feature] || new Set()).add(r.subFeature);
    });
    ['CarPlay', 'Android Auto', 'iPod'].forEach(feature => {
      const names = byFeature[feature];
      if (!names || !names.size) return;
      const optgroup = document.createElement('optgroup');
      optgroup.label = feature;
      Array.from(names).sort().forEach(full => {
        const opt = document.createElement('option');
        opt.value = full;
        opt.textContent = stripGroupPrefix(full);
        optgroup.appendChild(opt);
      });
      subFeatureSel.appendChild(optgroup);
    });
    const uncatOpt = document.createElement('option');
    uncatOpt.value = '未分類';
    uncatOpt.textContent = '未分類';
    subFeatureSel.appendChild(uncatOpt);
  })();

  const bugSortState = { key: '', dir: 'asc' };

  function renderBugTable() {
    let rows = BUGS;
    if (featureSel.value) rows = rows.filter(r => r.feature === featureSel.value);
    if (statusSel.value === 'done') rows = rows.filter(r => r.done);
    if (statusSel.value === 'not-done') rows = rows.filter(r => !r.done);
    if (labelSel.value) rows = rows.filter(r => r.labelBucket === labelSel.value);
    if (subFeatureSel.value) rows = rows.filter(r => r.subFeature === subFeatureSel.value);
    if (assigneeSel.value) rows = rows.filter(r => r.assignee === assigneeSel.value);
    if (severitySel.value) rows = rows.filter(r => r.severity === severitySel.value);
    if (prioritySel.value) rows = rows.filter(r => r.priority === prioritySel.value);
    const q = search.value.toLowerCase();
    if (q) rows = rows.filter(r => r.key.toLowerCase().includes(q) || r.summary.toLowerCase().includes(q));
    rows = sortRows(rows, bugSortState.key, bugSortState.dir);
    document.getElementById('bugMissingCaption').textContent = `共 ${rows.length} 張票 (Bug 總數 ${BUGS.length} 張)`;
    tbody.innerHTML = rows.length ? rows.map(r => `
      <tr>
        <td class="key"><a href="${ticketUrl(r.key)}" target="_blank">${r.key}</a></td>
        <td>${esc(r.feature)}</td>
        <td>${esc(stripGroupPrefix(r.subFeature))}</td>
        <td>${esc(r.assignee)}</td>
        <td>${esc(r.severity)}</td>
        <td>${esc(r.priority)}</td>
        <td>${bugStatusBadge(r)}</td>
        <td>${esc(r.labelBucket)}</td>
        <td>${esc(r.summary)}</td>
      </tr>
    `).join('') : '<tr><td colspan="9" class="empty-state">沒有符合條件的票</td></tr>';
  }
  [featureSel, statusSel, labelSel, subFeatureSel, assigneeSel, severitySel, prioritySel].forEach(el => el.addEventListener('change', renderBugTable));
  search.addEventListener('input', renderBugTable);
  attachSortHandlers(tbody.closest('table').querySelector('thead'), bugSortState, renderBugTable);
  renderBugTable();

  function jumpToBugSeverity(severity) {
    severitySel.value = severity;
    prioritySel.value = '';
    featureSel.value = '';
    subFeatureSel.value = '';
    assigneeSel.value = '';
    statusSel.value = 'not-done';
    labelSel.value = '';
    search.value = '';
    renderBugTable();
    tbody.closest('section.card').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function jumpToBugPriority(priority) {
    prioritySel.value = priority;
    severitySel.value = '';
    featureSel.value = '';
    subFeatureSel.value = '';
    assigneeSel.value = '';
    statusSel.value = 'not-done';
    labelSel.value = '';
    search.value = '';
    renderBugTable();
    tbody.closest('section.card').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function renderBugSeverityTiles() {
    const el = document.getElementById('bugSeverityTiles');
    el.innerHTML = '';
    const makeTile = (label, subset, clickValue) => {
      const d = subset.filter(r => r.done).length;
      const t = subset.length;
      const notDone = t - d;
      const p = t ? Math.round(d / t * 100) : 0;
      const tile = document.createElement('div');
      tile.className = clickValue !== null ? 'stat-tile stat-tile-clickable' : 'stat-tile';
      tile.innerHTML = `
        <div class="label">${esc(label)}</div>
        <div class="value">${notDone}</div>
        <div class="sub">未完成 · 完成率 ${p}%(${d} / ${t} 已完成)</div>
        <div class="meter"><div style="width:${p}%"></div></div>
      `;
      if (clickValue !== null) tile.addEventListener('click', () => jumpToBugSeverity(clickValue));
      el.appendChild(tile);
    };
    makeTile('Bug 總數', BUGS, null);
    SEVERITY_ORDER.filter(s => BUGS.some(r => r.severity === s)).forEach(sev => {
      makeTile(sev, BUGS.filter(r => r.severity === sev), sev);
    });
  }
  renderBugSeverityTiles();

  function renderBugPriorityTiles() {
    const el = document.getElementById('bugPriorityTiles');
    el.innerHTML = '';
    const makeTile = (label, subset, clickValue) => {
      const d = subset.filter(r => r.done).length;
      const t = subset.length;
      const notDone = t - d;
      const p = t ? Math.round(d / t * 100) : 0;
      const tile = document.createElement('div');
      tile.className = clickValue !== null ? 'stat-tile stat-tile-clickable' : 'stat-tile';
      tile.innerHTML = `
        <div class="label">${esc(label)}</div>
        <div class="value">${notDone}</div>
        <div class="sub">未完成 · 完成率 ${p}%(${d} / ${t} 已完成)</div>
        <div class="meter"><div style="width:${p}%"></div></div>
      `;
      if (clickValue !== null) tile.addEventListener('click', () => jumpToBugPriority(clickValue));
      el.appendChild(tile);
    };
    makeTile('Bug 總數', BUGS, null);
    PRIORITY_ORDER.filter(p => BUGS.some(r => r.priority === p)).forEach(pri => {
      makeTile(pri, BUGS.filter(r => r.priority === pri), pri);
    });
  }
  renderBugPriorityTiles();

  function jumpToBugAssignee(assignee) {
    assigneeSel.value = assignee;
    featureSel.value = '';
    subFeatureSel.value = '';
    severitySel.value = '';
    prioritySel.value = '';
    statusSel.value = 'not-done';
    labelSel.value = '';
    search.value = '';
    renderBugTable();
    tbody.closest('section.card').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function jumpToBugSubFeature(feature, fullSubFeature) {
    featureSel.value = feature;
    subFeatureSel.value = fullSubFeature;
    assigneeSel.value = '';
    severitySel.value = '';
    prioritySel.value = '';
    statusSel.value = 'not-done';
    labelSel.value = '';
    search.value = '';
    renderBugTable();
    tbody.closest('section.card').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function renderBugSubFeatureBars() {
    SUBFEATURE_GROUPS.forEach(group => {
      const el = document.getElementById('bugSubFeatureBars-' + group.elId);
      const notDone = BUGS.filter(r => !r.done && r.feature === group.feature);
      const total = notDone.length;
      document.getElementById('bugSubFeatureBarsCaption-' + group.elId).textContent =
        `在 ${total} 張未完成的 ${group.feature} Bug 中,依功能子分類(cpaa-feature-taxonomy)統計的票數;無法明確對應到子分類的票歸在「未分類」`;
      const counts = {};
      notDone.forEach(r => { counts[r.subFeature] = (counts[r.subFeature] || 0) + 1; });
      const rows = Object.keys(counts)
        .map(name => ({ name: stripGroupPrefix(name), fullName: name, count: counts[name] }))
        .sort((a, b) => b.count - a.count);
      el.innerHTML = '';
      rows.forEach(row => {
        const pct = total ? Math.round(row.count / total * 100) : 0;
        const color = row.fullName === '未分類' ? 'var(--muted)' : group.color;
        const div = document.createElement('div');
        div.className = 'bar-row bar-row-pct bar-row-clickable';
        div.title = `點擊查看「${row.name}」的票`;
        div.innerHTML = `
          <div class="name wide" title="${esc(row.name)}">${esc(row.name)}</div>
          <div class="pct-value" style="color:${color}">${pct}%</div>
          <div class="bar-count">${row.count}</div>
        `;
        div.addEventListener('click', () => jumpToBugSubFeature(group.feature, row.fullName));
        el.appendChild(div);
      });
    });
  }
  renderBugSubFeatureBars();

  function renderBugAssigneeBars() {
    const container = document.getElementById('bugAssigneeBarsContainer');
    container.innerHTML = '';
    const notDone = BUGS.filter(r => !r.done);
    const teamsPresent = TEAM_ORDER.filter(team => notDone.some(r => r.team === team));
    teamsPresent.forEach(team => {
      const teamRows = notDone.filter(r => r.team === team);
      const t = teamRows.length;
      const counts = {};
      teamRows.forEach(r => { counts[r.assignee] = (counts[r.assignee] || 0) + 1; });
      const rows = Object.keys(counts)
        .map(name => ({ name, count: counts[name] }))
        .sort((a, b) => b.count - a.count);

      const col = document.createElement('div');
      col.style.cssText = 'flex:1 1 260px; min-width:260px; max-width:100%; overflow:hidden;';
      col.innerHTML = `
        <h3 style="margin:0 0 4px; font-size:14px;">${esc(team)}</h3>
        <p class="caption">在 ${t} 張未完成 Bug 中,依 assignee 統計的票數</p>
        <div class="bars-target"></div>
      `;
      const target = col.querySelector('.bars-target');
      rows.forEach(row => {
        const pct2 = t ? Math.round(row.count / t * 100) : 0;
        const div = document.createElement('div');
        div.className = 'bar-row bar-row-pct bar-row-clickable';
        div.title = `點擊查看 ${row.name} 的票`;
        div.innerHTML = `
          <div class="name assignee" title="${esc(row.name)}">${esc(row.name)}</div>
          <div class="pct-value" style="color:var(--series-cp)">${pct2}%</div>
          <div class="bar-count">${row.count}</div>
        `;
        div.addEventListener('click', () => jumpToBugAssignee(row.name));
        target.appendChild(div);
      });
      container.appendChild(col);
    });
  }
  renderBugAssigneeBars();
}

const AUDIO_GROUPS = ['SWE2', 'SWE3', 'SWE5', 'Bug'];
const AUDIO_GROUP_COLORS = {
  SWE2: 'var(--series-cp)',
  SWE3: 'var(--series-aa)',
  SWE5: 'var(--series-ipod)',
  Bug: 'var(--critical)',
  Other: 'var(--muted)',
};

function renderAudioPanel() {
  const panel = document.getElementById('panel-Audio');
  const done = AUDIO.filter(r => r.done).length;
  const total = AUDIO.length;
  const notDone = total - done;
  const pct = total ? Math.round(done / total * 100) : 0;

  const groupRows = [...AUDIO_GROUPS, 'Other'].map(g => {
    const subset = AUDIO.filter(r => r.group === g);
    const gDone = subset.filter(r => r.done).length;
    return { group: g, total: subset.length, done: gDone, notDone: subset.length - gDone };
  }).filter(g => g.total > 0);

  panel.innerHTML = `
    <div class="stat-row">
      <div class="stat-tile">
        <div class="label">未完成數量</div>
        <div class="value">${notDone}</div>
        <div class="sub">完成率 ${pct}%（${done} / ${total} 已完成）</div>
        <div class="meter"><div style="width:${pct}%"></div></div>
      </div>
    </div>
    <section class="card">
      <h2>依 SWE2 / SWE3 / SWE5 / Bug 分類</h2>
      <p class="caption">summary 中含有「audio」的票,依 Issue Type 為 Bug,或 summary 中的 SWE 標記分類(另有少量未分類的票一併列出,SWE1 不列入統計)。其中 SWE2 只挑出 Label 包含「HighPriDep」的項目,SWE3/SWE5/Bug 不受此限</p>
      <div class="stat-row">
        ${groupRows.map(g => `
          <div class="stat-tile stat-tile-clickable" data-group="${esc(g.group)}">
            <div class="label">${g.group}</div>
            <div class="value">${g.notDone}</div>
            <div class="sub">未完成 · 共 ${g.total} 張,${g.done} 已完成 (${g.total ? Math.round(g.done/g.total*100) : 0}%)</div>
          </div>
        `).join('')}
      </div>
    </section>
    <section class="card">
      <h2>Audio 票清單(僅未完成)</h2>
      <p class="caption" id="audioCaption"></p>
      <div class="chip-row" id="audioAssigneeChips"></div>
      <div class="filters">
        <select id="audioGroupFilter">
          <option value="">全部分類</option>
          ${[...AUDIO_GROUPS, 'Other'].map(g => `<option value="${g}">${g}</option>`).join('')}
        </select>
        <input type="text" id="audioSearch" placeholder="搜尋 key 或 summary...">
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th data-sort="key">Key</th><th data-sort="group">分類</th><th data-sort="issueType">Issue Type</th>
            <th data-sort="status">Status</th><th data-sort="assignee">Assignee</th><th data-sort="summary">Summary</th>
          </tr></thead>
          <tbody id="audioTbody"></tbody>
        </table>
      </div>
    </section>
  `;

  const groupSel = document.getElementById('audioGroupFilter');
  const search = document.getElementById('audioSearch');
  const tbody = document.getElementById('audioTbody');
  const chipRow = document.getElementById('audioAssigneeChips');
  let selectedAssignee = '';

  const AUDIO_NOT_DONE = AUDIO.filter(r => !r.done);

  // Build the assignee chip row: "全部" plus one chip per assignee, each showing their count.
  const assigneeCounts = {};
  AUDIO_NOT_DONE.forEach(r => { assigneeCounts[r.assignee] = (assigneeCounts[r.assignee] || 0) + 1; });
  const assignees = Object.keys(assigneeCounts).sort((a, b) => assigneeCounts[b] - assigneeCounts[a]);
  function renderChips() {
    const all = [{ name: '', label: `全部 (${AUDIO_NOT_DONE.length})` }, ...assignees.map(a => ({ name: a, label: `${a} (${assigneeCounts[a]})` }))];
    chipRow.innerHTML = all.map(c => `<button type="button" class="chip${c.name === selectedAssignee ? ' active' : ''}" data-assignee="${esc(c.name)}">${esc(c.label)}</button>`).join('');
    chipRow.querySelectorAll('.chip').forEach(btn => {
      btn.addEventListener('click', () => {
        selectedAssignee = btn.dataset.assignee;
        renderChips();
        renderAudioTable();
      });
    });
  }

  function rowHtml(r) {
    return `
      <tr>
        <td class="key"><a href="${ticketUrl(r.key)}" target="_blank">${r.key}</a></td>
        <td>${esc(r.group)}</td>
        <td>${esc(r.issueType)}</td>
        <td>${statusBadge(r)}</td>
        <td>${esc(r.assignee)}</td>
        <td>${esc(r.summary)}</td>
      </tr>
    `;
  }

  const audioSortState = { key: '', dir: 'asc' };

  function renderAudioTable() {
    let rows = AUDIO_NOT_DONE;
    if (selectedAssignee) rows = rows.filter(r => r.assignee === selectedAssignee);
    if (groupSel.value) rows = rows.filter(r => r.group === groupSel.value);
    const q = search.value.toLowerCase();
    if (q) rows = rows.filter(r => r.key.toLowerCase().includes(q) || r.summary.toLowerCase().includes(q));
    document.getElementById('audioCaption').textContent = `共 ${rows.length} 張未完成票 (Audio 未完成總數 ${AUDIO_NOT_DONE.length} 張)`;

    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty-state">沒有符合條件的票</td></tr>';
      return;
    }

    if (audioSortState.key) {
      // A sort column is active — always show a flat sorted list, bypassing assignee grouping.
      tbody.innerHTML = sortRows(rows, audioSortState.key, audioSortState.dir).map(rowHtml).join('');
      return;
    }

    if (selectedAssignee) {
      // A single person is selected — flat list, no need to re-group.
      tbody.innerHTML = rows.map(rowHtml).join('');
      return;
    }

    // No assignee chip selected — group the rows by assignee, ordered by group size.
    const byAssignee = {};
    rows.forEach(r => { (byAssignee[r.assignee] = byAssignee[r.assignee] || []).push(r); });
    const orderedAssignees = Object.keys(byAssignee).sort((a, b) => byAssignee[b].length - byAssignee[a].length);
    tbody.innerHTML = orderedAssignees.map(a => {
      const grp = byAssignee[a];
      return `<tr><td colspan="6" class="group-header">${esc(a)} — 未完成 ${grp.length} 張</td></tr>` + grp.map(rowHtml).join('');
    }).join('');
  }

  renderChips();
  [groupSel].forEach(el => el.addEventListener('change', renderAudioTable));
  search.addEventListener('input', renderAudioTable);
  attachSortHandlers(tbody.closest('table').querySelector('thead'), audioSortState, renderAudioTable);
  renderAudioTable();

  panel.querySelectorAll('.stat-tile[data-group]').forEach(tile => {
    tile.addEventListener('click', () => {
      groupSel.value = tile.dataset.group;
      selectedAssignee = '';
      search.value = '';
      renderChips();
      renderAudioTable();
      tbody.closest('section.card').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

function renderPretestPanel() {
  const panel = document.getElementById('panel-Pretest');
  panel.innerHTML = `
    <div class="stat-row" id="pretestTiles"></div>
    <section class="card">
      <h2>Pretest 清單(Bug 票中 title 含「PCTS」或「Facet」)</h2>
      <p class="caption" id="pretestCaption"></p>
      <div class="filters">
        <select id="pretestGroupFilter">
          <option value="">全部分類</option>
          <option value="CP (Facet)">CP (Facet)</option>
          <option value="AA (PCTS)">AA (PCTS)</option>
        </select>
        <select id="pretestStatusFilter">
          <option value="">全部狀態</option>
          <option value="done">已完成</option>
          <option value="not-done">未完成</option>
        </select>
        <select id="pretestSeverityFilter">
          <option value="">全部 Severity</option>
        </select>
        <input type="text" id="pretestSearch" placeholder="搜尋 key 或 summary...">
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th data-sort="key">Key</th><th data-sort="pretestGroup">分類</th><th data-sort="assignee">Assignee</th>
            <th data-sort="severity">Severity</th><th data-sort="status">Status</th><th data-sort="summary">Summary</th>
          </tr></thead>
          <tbody id="pretestTbody"></tbody>
        </table>
      </div>
    </section>
  `;

  function renderPretestTiles() {
    const el = document.getElementById('pretestTiles');
    el.innerHTML = '';
    const makeTile = (label, subset, clickValue) => {
      const d = subset.filter(r => r.done).length;
      const t = subset.length;
      const notDone = t - d;
      const p = t ? Math.round(d / t * 100) : 0;
      const tile = document.createElement('div');
      tile.className = 'stat-tile stat-tile-clickable';
      tile.innerHTML = `
        <div class="label">${esc(label)}</div>
        <div class="value">${notDone}</div>
        <div class="sub">未完成 · 完成率 ${p}%(${d} / ${t} 已完成)</div>
        <div class="meter"><div style="width:${p}%"></div></div>
      `;
      tile.addEventListener('click', () => jumpToPretestGroup(clickValue));
      el.appendChild(tile);
    };
    makeTile('CP (Facet)', PRETEST.filter(r => r.pretestGroup === 'CP (Facet)'), 'CP (Facet)');
    makeTile('AA (PCTS)', PRETEST.filter(r => r.pretestGroup === 'AA (PCTS)'), 'AA (PCTS)');
  }
  renderPretestTiles();

  const groupSel = document.getElementById('pretestGroupFilter');
  const statusSel = document.getElementById('pretestStatusFilter');
  const severitySel = document.getElementById('pretestSeverityFilter');
  const search = document.getElementById('pretestSearch');
  const tbody = document.getElementById('pretestTbody');

  (function populateSeverityFilter() {
    SEVERITY_ORDER.filter(s => PRETEST.some(r => r.severity === s)).forEach(sev => {
      const opt = document.createElement('option');
      opt.value = sev;
      opt.textContent = sev;
      severitySel.appendChild(opt);
    });
  })();

  const pretestSortState = { key: '', dir: 'asc' };

  function renderPretestTable() {
    let rows = PRETEST;
    if (groupSel.value) rows = rows.filter(r => r.pretestGroup === groupSel.value);
    if (statusSel.value === 'done') rows = rows.filter(r => r.done);
    if (statusSel.value === 'not-done') rows = rows.filter(r => !r.done);
    if (severitySel.value) rows = rows.filter(r => r.severity === severitySel.value);
    const q = search.value.toLowerCase();
    if (q) rows = rows.filter(r => r.key.toLowerCase().includes(q) || r.summary.toLowerCase().includes(q));
    rows = sortRows(rows, pretestSortState.key, pretestSortState.dir);
    document.getElementById('pretestCaption').textContent = `共 ${rows.length} 張票 (Pretest 總數 ${PRETEST.length} 張)`;
    tbody.innerHTML = rows.length ? rows.map(r => `
      <tr>
        <td class="key"><a href="${ticketUrl(r.key)}" target="_blank">${r.key}</a></td>
        <td>${esc(r.pretestGroup)}</td>
        <td>${esc(r.assignee)}</td>
        <td>${esc(r.severity)}</td>
        <td>${bugStatusBadge(r)}</td>
        <td>${esc(r.summary)}</td>
      </tr>
    `).join('') : '<tr><td colspan="6" class="empty-state">沒有符合條件的票</td></tr>';
  }
  [groupSel, statusSel, severitySel].forEach(el => el.addEventListener('change', renderPretestTable));
  search.addEventListener('input', renderPretestTable);
  attachSortHandlers(tbody.closest('table').querySelector('thead'), pretestSortState, renderPretestTable);
  renderPretestTable();

  function jumpToPretestGroup(group) {
    groupSel.value = group;
    statusSel.value = 'not-done';
    severitySel.value = '';
    search.value = '';
    renderPretestTable();
    tbody.closest('section.card').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function initTabs() {
  const buttons = document.querySelectorAll('nav.tabs button');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      document.getElementById('panel-' + btn.dataset.tab).classList.add('active');
    });
  });
}

document.getElementById('themeToggle').addEventListener('click', () => {
  const root = document.documentElement;
  const cur = root.getAttribute('data-theme');
  root.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark');
});

renderCompletion();
renderSubFeatureBars();
renderAssigneeBars();
populateMissingSubFeatureFilter();
populateMissingAssigneeFilter();
renderMissingTable();
document.getElementById('missingSweFilter').addEventListener('change', renderMissingTable);
document.getElementById('missingFeatureFilter').addEventListener('change', renderMissingTable);
document.getElementById('missingStatusFilter').addEventListener('change', renderMissingTable);
document.getElementById('missingLabelFilter').addEventListener('change', renderMissingTable);
document.getElementById('missingSubFeatureFilter').addEventListener('change', renderMissingTable);
document.getElementById('missingAssigneeFilter').addEventListener('change', renderMissingTable);
document.getElementById('missingSearch').addEventListener('input', renderMissingTable);
attachSortHandlers(document.getElementById('missingTbody').closest('table').querySelector('thead'), missingSortState, renderMissingTable);
renderBugPanel();
renderAudioPanel();
renderPretestPanel();
initTabs();
</script>
</body>
</html>
"""

html = HTML_TEMPLATE.replace("__DATA_JSON__", DATA_JSON).replace("__TOTAL__", str(len(DATA["tickets"]))).replace("__BUGTOTAL__", str(len(DATA["bugs"]))).replace("__UPDATED_AT__", UPDATED_AT)

with open("dashboard.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Wrote dashboard.html,", len(html), "bytes")
