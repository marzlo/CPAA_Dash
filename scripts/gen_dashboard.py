import json
from datetime import datetime

with open("dashboard_data.json", encoding="utf-8") as f:
    DATA = json.load(f)

try:
    with open("history.json", encoding="utf-8") as f:
        HISTORY = json.load(f)
except FileNotFoundError:
    HISTORY = {}

DATA["history"] = HISTORY

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
  .toggle-row {
    position: absolute; top: 20px; right: 28px;
    display: flex; gap: 8px;
  }
  .theme-toggle, .lang-toggle {
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
<div class="toggle-row">
  <button class="lang-toggle" id="langToggle">中文 / EN</button>
  <button class="theme-toggle" id="themeToggle">🌓 Theme</button>
</div>
<header>
  <h1 id="headerTitle"></h1>
  <p id="headerSubtitle"></p>
  <p style="margin-top:4px; font-weight:600;" id="headerUpdatedAt"></p>
</header>
<nav class="tabs" id="tabs">
  <button data-tab="overview" data-i18n-tab="overview" class="active">Overview</button>
  <button data-tab="Bug" data-i18n-tab="bug">Bug</button>
  <button data-tab="Audio" data-i18n-tab="audio">Audio</button>
  <button data-tab="Pretest" data-i18n-tab="pretest">Pretest</button>
</nav>
<main>

  <div class="panel active" id="panel-overview">
    <div class="stat-row" id="completionTiles"></div>

    <section class="card">
      <h2 data-i18n="ov_trend_heading"></h2>
      <p class="caption" id="trendCaption"></p>
      <div id="trendChartWrap"></div>
    </section>

    <section class="card">
      <h2 data-i18n="ov_aging_heading"></h2>
      <p class="caption" id="agingCaption"></p>
      <div id="agingBars"></div>
    </section>

    <section class="card">
      <h2 data-i18n="ov_buginflow_heading"></h2>
      <p class="caption" id="bugInflowCaption"></p>
      <div id="bugInflowChartWrap"></div>
    </section>

    <section class="card">
      <h2 data-i18n="ov_subfeature_heading"></h2>
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
      <h2 data-i18n="ov_assignee_heading"></h2>
      <p class="caption" data-i18n="team_map_note"></p>
      <div id="assigneeBarsContainer" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:24px;"></div>
    </section>

    <section class="card">
      <h2 data-i18n="ov_list_heading"></h2>
      <p class="caption" id="missingCaption"></p>
      <div class="filters">
        <select id="missingSweFilter">
          <option value="" data-i18n="all_swe"></option>
          <option value="SWE2">SWE2</option>
          <option value="SWE3">SWE3</option>
          <option value="SWE5">SWE5</option>
        </select>
        <select id="missingFeatureFilter">
          <option value="" data-i18n="all_feature"></option>
          <option value="CarPlay">CarPlay</option>
          <option value="Android Auto">Android Auto</option>
          <option value="iPod">iPod</option>
        </select>
        <select id="missingStatusFilter">
          <option value="" data-i18n="all_status"></option>
          <option value="done" data-i18n="status_done"></option>
          <option value="not-done" data-i18n="status_not_done"></option>
        </select>
        <select id="missingLabelFilter">
          <option value="" data-i18n="all_label_bucket"></option>
          <option value="ASW-R2">ASW-R2</option>
          <option value="ASW-R3 (不含CPAA 0830)" data-i18n="label_bucket_asw_r3"></option>
          <option value="CPAA0830">CPAA0830</option>
          <option value="三者皆無" selected data-i18n="label_bucket_none"></option>
        </select>
        <select id="missingSubFeatureFilter">
          <option value="" data-i18n="all_subfeature"></option>
        </select>
        <select id="missingAssigneeFilter">
          <option value="" data-i18n="all_assignee"></option>
        </select>
        <input type="text" id="missingSearch" data-i18n-placeholder="search_placeholder">
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th data-sort="key">Key</th><th data-sort="swe">SWE</th><th data-sort="feature" data-i18n="th_feature"></th>
            <th data-sort="subFeature" data-i18n="th_subfeature"></th><th data-sort="assignee" data-i18n="th_assignee"></th>
            <th data-sort="status" data-i18n="th_status"></th><th data-sort="labelBucket" data-i18n="th_label_bucket"></th><th data-sort="summary" data-i18n="th_summary"></th>
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
const UPDATED_AT = "__UPDATED_AT__";
const DATA = RAW.tickets;
const BUGS = RAW.bugs;
const AUDIO = RAW.audio;
const PRETEST = RAW.pretest;
const HISTORY = RAW.history || {};
const FEATURE_COLORS = { "CarPlay": "var(--series-cp)", "Android Auto": "var(--series-aa)", "iPod": "var(--series-ipod)" };

// ---- i18n ----------------------------------------------------------------
// Only UI chrome (headings, captions, filter labels, table headers, badges)
// is translated. Actual Jira data (ticket keys, summaries, assignees, real
// Jira status text, sub-feature taxonomy names, team codes) is left as-is —
// translating that would misrepresent the source data.
let LANG = 'zh';
try {
  const saved = localStorage.getItem('cpaaDashboardLang');
  if (saved === 'zh' || saved === 'en') LANG = saved;
} catch (e) { /* localStorage unavailable — default to zh */ }

const STRINGS = {
  headerTitle: { zh: 'CPAA SWE3 / SWE5 票務儀表板', en: 'CPAA SWE3 / SWE5 Ticket Dashboard' },
  headerSubtitle: {
    zh: (total, bugTotal) => `Mobile Drive · Jira project NR1LT · filter 12399 · 資料來源:使用者匯出的 Jira Excel (CPAA_general_ticket),共 ${total} 張 SWE3/SWE5 票、${bugTotal} 張 Bug 票`,
    en: (total, bugTotal) => `Mobile Drive · Jira project NR1LT · filter 12399 · Source: user-exported Jira Excel (CPAA_general_ticket) — ${total} SWE3/SWE5 tickets, ${bugTotal} Bug tickets`,
  },
  headerUpdatedAt: { zh: d => `最後更新日期:${d}`, en: d => `Last updated: ${d}` },
  tab_overview: { zh: '總覽', en: 'Overview' },
  tab_bug: { zh: 'Bug', en: 'Bug' },
  tab_audio: { zh: 'Audio', en: 'Audio' },
  tab_pretest: { zh: 'Pretest', en: 'Pretest' },

  ov_subfeature_heading: { zh: 'Sub-feature 分佈(僅未完成票,SWE2+SWE3+SWE5 合併計算,依 CarPlay/Android Auto/iPod 分欄)', en: 'Sub-feature breakdown (not-done tickets only, SWE2+SWE3+SWE5 combined, split by CarPlay/Android Auto/iPod)' },
  ov_assignee_heading: { zh: 'Assignee 分佈(僅未完成票,SWE2+SWE3+SWE5 合併計算,依組織分欄)', en: 'Assignee breakdown (not-done tickets only, SWE2+SWE3+SWE5 combined, split by team)' },
  team_map_note: { zh: '組織對應依據 cpaa-dashboard skill 的 TEAM_MAP;沒有對應到組織的人歸在「Unknown」', en: 'Team mapping follows the cpaa-dashboard skill’s TEAM_MAP; anyone not mapped falls under "Unknown"' },
  ov_list_heading: { zh: '票清單(依 Label 分類篩選)', en: 'Ticket list (filter by label category)' },

  ov_trend_heading: { zh: '進度趨勢(燃盡圖 · 未完成票數隨時間變化)', en: 'Progress trend (burndown · not-done count over time)' },
  trend_caption: { zh: (a, b) => `每日快照,${a} ~ ${b}(每天自動記錄一次;資料從此功能上線那天開始累積,無法回溯更早的歷史)`, en: (a, b) => `Daily snapshots, ${a} – ${b} (recorded automatically once per day; history starts from when this feature was deployed and can't be backfilled further)` },
  trend_insufficient_body: { zh: '目前累積的快照天數還不夠畫趨勢線。系統會從今天開始每天自動記錄一筆,幾天後這裡就會出現趨勢圖', en: "Not enough daily snapshots yet to draw a trend line. One is recorded automatically every day starting today, so a trend will appear here after a few days" },

  ov_aging_heading: { zh: '未完成票的卡住天數分佈(SWE2/3/5 + Bug 合併)', en: 'Age distribution of not-done tickets (SWE2/3/5 + Bug combined)' },
  aging_caption: { zh: (total, unknown) => `共 ${total} 張未完成票,依建立日期至今的天數分佈${unknown ? `(其中 ${unknown} 張沒有建立日期資料,未計入)` : ''}`, en: (total, unknown) => `${total} not-done tickets, bucketed by days since creation${unknown ? ` (${unknown} without a creation date, excluded)` : ''}` },
  aging_0_7: { zh: '0-7 天', en: '0-7 days' },
  aging_8_14: { zh: '8-14 天', en: '8-14 days' },
  aging_15_30: { zh: '15-30 天', en: '15-30 days' },
  aging_30_plus: { zh: '超過 30 天', en: 'Over 30 days' },

  ov_buginflow_heading: { zh: 'Bug 每週新增數量(近 12 週,依建立日期)', en: 'Weekly new bugs (last 12 weeks, by creation date)' },
  buginflow_caption: { zh: (a, b) => `ISO 週次 ${a} ~ ${b}`, en: (a, b) => `ISO week ${a} – ${b}` },
  buginflow_no_data: { zh: '目前的資料沒有建立日期欄位,無法統計', en: 'No creation-date data available to chart' },

  all_swe: { zh: '全部 SWE', en: 'All SWE' },
  all_feature: { zh: '全部 Feature', en: 'All Features' },
  all_status: { zh: '全部狀態', en: 'All Statuses' },
  status_done: { zh: '已完成', en: 'Done' },
  status_not_done: { zh: '未完成', en: 'Not done' },
  all_label_bucket: { zh: '全部 Label 分類', en: 'All Label Categories' },
  label_bucket_asw_r3: { zh: 'ASW-R3 (不含CPAA 0830)', en: 'ASW-R3 (excl. CPAA 0830)' },
  label_bucket_none: { zh: '三者皆無', en: 'None of the above' },
  all_subfeature: { zh: '全部 Sub-feature', en: 'All Sub-features' },
  all_assignee: { zh: '全部 Assignee', en: 'All Assignees' },
  all_severity: { zh: '全部 Severity', en: 'All Severities' },
  all_priority: { zh: '全部 Priority', en: 'All Priorities' },
  all_group: { zh: '全部分類', en: 'All Categories' },
  search_placeholder: { zh: '搜尋 key 或 summary...', en: 'Search key or summary...' },

  th_feature: { zh: 'Feature', en: 'Feature' },
  th_subfeature: { zh: 'Sub-feature', en: 'Sub-feature' },
  th_assignee: { zh: 'Assignee', en: 'Assignee' },
  th_status: { zh: 'Status', en: 'Status' },
  th_label_bucket: { zh: 'Label 分類', en: 'Label Category' },
  th_summary: { zh: 'Summary', en: 'Summary' },
  th_severity: { zh: 'Severity', en: 'Severity' },
  th_priority: { zh: 'Priority', en: 'Priority' },
  th_group: { zh: '分類', en: 'Category' },
  th_issue_type: { zh: 'Issue Type', en: 'Issue Type' },

  empty_state: { zh: '沒有符合條件的票', en: 'No tickets match the current filters' },
  uncategorized: { zh: '未分類', en: 'Uncategorized' },
  severity_unspecified: { zh: '未標示', en: 'Unspecified' },

  swe_completion_label: { zh: swe => `${swe} 完成率`, en: swe => `${swe} completion` },
  swe_total_label: { zh: '合計 (SWE2+SWE3+SWE5)', en: 'Total (SWE2+SWE3+SWE5)' },
  tile_sub: { zh: (d, t, p) => `未完成 · 完成率 ${p}%(${d} / ${t} 已完成)`, en: (d, t, p) => `Not done · ${p}% complete (${d} / ${t} done)` },

  jump_tooltip: { zh: name => `點擊查看「${name}」的票`, en: name => `Click to view tickets for "${name}"` },
  jump_tooltip_plain: { zh: name => `點擊查看 ${name} 的票`, en: name => `Click to view ${name}'s tickets` },
  assignee_caption: { zh: total => `在 ${total} 張未完成票中,依 assignee 統計的票數`, en: total => `Ticket counts by assignee, out of ${total} not-done tickets` },
  subfeature_caption: { zh: (total, feature) => `在 ${total} 張未完成的 ${feature} 票中(SWE2+SWE3+SWE5 合併),依功能子分類(cpaa-feature-taxonomy)統計的票數;無法明確對應到子分類的票歸在「未分類」`, en: (total, feature) => `Ticket counts by sub-feature (cpaa-feature-taxonomy), out of ${total} not-done ${feature} tickets (SWE2+SWE3+SWE5 combined); tickets that can't be clearly matched fall under "Uncategorized"` },
  missing_caption: { zh: (n, total) => `共 ${n} 張票 (DATA 總數 ${total} 張,含已完成與未完成)`, en: (n, total) => `${n} tickets shown (out of ${total} total, done and not-done included)` },

  bug_priority_bug_total: { zh: 'Bug 總數', en: 'Total Bugs' },
  bug_label_heading: { zh: 'Label 分佈(僅未完成 Bug)', en: 'Label breakdown (not-done Bugs only)' },
  bug_subfeature_heading: { zh: 'Sub-feature 分佈(僅未完成 Bug,依 CarPlay/Android Auto/iPod 分欄)', en: 'Sub-feature breakdown (not-done Bugs only, split by CarPlay/Android Auto/iPod)' },
  bug_assignee_heading: { zh: 'Assignee 分佈(僅未完成 Bug,依組織分欄)', en: 'Assignee breakdown (not-done Bugs only, split by team)' },
  bug_list_heading: { zh: 'Bug 清單(依 Feature / Label 分類篩選)', en: 'Bug list (filter by feature / label category)' },
  bug_label_caption: { zh: t => `在 ${t} 張未完成的 Bug 票中,依標籤分類的票數(每張票只計入一類,依 ASW-R2 → ASW-R3(不含CPAA 0830) → CPAA0830 → 三者皆無 的優先順序判斷)`, en: t => `Ticket counts by label category, out of ${t} not-done Bugs (each ticket counted once, priority order: ASW-R2 → ASW-R3 (excl. CPAA 0830) → CPAA0830 → none of the above)` },
  bug_subfeature_caption: { zh: (total, feature) => `在 ${total} 張未完成的 ${feature} Bug 中,依功能子分類(cpaa-feature-taxonomy)統計的票數;無法明確對應到子分類的票歸在「未分類」`, en: (total, feature) => `Ticket counts by sub-feature (cpaa-feature-taxonomy), out of ${total} not-done ${feature} Bugs; tickets that can't be clearly matched fall under "Uncategorized"` },
  bug_assignee_caption: { zh: t => `在 ${t} 張未完成 Bug 中,依 assignee 統計的票數`, en: t => `Ticket counts by assignee, out of ${t} not-done Bugs` },
  bug_missing_caption: { zh: n => `共 ${n} 張票 (Bug 總數 ${BUGS.length} 張)`, en: n => `${n} tickets shown (out of ${BUGS.length} Bugs total)` },

  audio_not_done_count: { zh: '未完成數量', en: 'Not-done count' },
  audio_pct_sub: { zh: (p, d, t) => `完成率 ${p}%(${d} / ${t} 已完成)`, en: (p, d, t) => `${p}% complete (${d} / ${t} done)` },
  audio_group_heading: { zh: '依 SWE2 / SWE3 / SWE5 / Bug 分類', en: 'By SWE2 / SWE3 / SWE5 / Bug category' },
  audio_group_desc: { zh: 'summary 中含有「audio」的票,依 Issue Type 為 Bug,或 summary 中的 SWE 標記分類(另有少量未分類的票一併列出,SWE1 不列入統計)。其中 SWE2 只挑出 Label 包含「HighPriDep」的項目,SWE3/SWE5/Bug 不受此限', en: 'Tickets whose summary mentions "audio", categorized by Issue Type = Bug or by the SWE tag in the summary (a small number of uncategorized tickets are also listed; SWE1 is excluded from the count). SWE2 is restricted to items with a "HighPriDep" label; SWE3/SWE5/Bug are not' },
  audio_group_sub: { zh: (notDone, total, done, pct) => `未完成 · 共 ${total} 張,${done} 已完成 (${pct}%)`, en: (notDone, total, done, pct) => `Not done · ${total} total, ${done} done (${pct}%)` },
  audio_list_heading: { zh: 'Audio 票清單(僅未完成)', en: 'Audio ticket list (not-done only)' },
  audio_chip_all: { zh: n => `全部 (${n})`, en: n => `All (${n})` },
  audio_caption: { zh: (n, total) => `共 ${n} 張未完成票 (Audio 未完成總數 ${total} 張)`, en: (n, total) => `${n} not-done tickets shown (out of ${total} not-done Audio tickets total)` },
  audio_group_header_row: { zh: (name, n) => `${name} — 未完成 ${n} 張`, en: (name, n) => `${name} — ${n} not done` },

  pretest_list_heading: { zh: 'Pretest 清單(Bug 票中 title 含「PCTS」或「Facet」)', en: 'Pretest list (Bug tickets whose title contains "PCTS" or "Facet")' },
  pretest_caption: { zh: n => `共 ${n} 張票 (Pretest 總數 ${PRETEST.length} 張)`, en: n => `${n} tickets shown (out of ${PRETEST.length} Pretest tickets total)` },
};

function t(key, ...args) {
  const entry = STRINGS[key];
  if (!entry) return key;
  const v = entry[LANG] ?? entry.zh;
  return typeof v === 'function' ? v(...args) : v;
}

// Display-only translation for a handful of enumerated Chinese values that are
// baked into the data (labelBucket / severity / priority / subFeature). The
// underlying value used for filtering/matching is never changed — only what
// the user sees is swapped per language.
function labelBucketText(v) {
  if (v === 'ASW-R3 (不含CPAA 0830)') return t('label_bucket_asw_r3');
  if (v === '三者皆無') return t('label_bucket_none');
  return v;
}
function severityText(v) {
  return v === '未標示' ? t('severity_unspecified') : v;
}
function subFeatureDisplay(name) {
  return name === '未分類' ? t('uncategorized') : stripGroupPrefix(name);
}

function applyStaticI18n() {
  document.documentElement.lang = LANG === 'zh' ? 'zh-Hant' : 'en';
  document.getElementById('langToggle').textContent = LANG === 'zh' ? '中文 / EN' : 'EN / 中文';
  document.getElementById('headerTitle').textContent = t('headerTitle');
  document.title = t('headerTitle');
  document.getElementById('headerSubtitle').textContent = t('headerSubtitle', DATA.length, BUGS.length);
  document.getElementById('headerUpdatedAt').textContent = t('headerUpdatedAt', UPDATED_AT);
  document.querySelectorAll('[data-i18n-tab]').forEach(el => { el.textContent = t('tab_' + el.dataset.i18nTab); });
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder); });
}

function esc(s) {
  return (s || "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
}
function statusBadge(rec) {
  if (rec.done) return '<span class="badge done">' + esc(t('status_done')) + '</span>';
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
  el.innerHTML = '';
  ['SWE2', 'SWE3', 'SWE5'].forEach(swe => {
    const subset = DATA.filter(r => r.swe === swe);
    const done = subset.filter(r => r.done).length;
    const total = subset.length;
    const notDone = total - done;
    const pct = total ? Math.round(done / total * 100) : 0;
    const tile = document.createElement('div');
    tile.className = 'stat-tile stat-tile-clickable';
    tile.innerHTML = `
      <div class="label">${esc(t('swe_completion_label', swe))}</div>
      <div class="value">${notDone}</div>
      <div class="sub">${esc(t('tile_sub', done, total, pct))}</div>
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
    <div class="label">${esc(t('swe_total_label'))}</div>
    <div class="value">${totalNotDone}</div>
    <div class="sub">${esc(t('tile_sub', totalDone, DATA.length, totalPct))}</div>
    <div class="meter"><div style="width:${totalPct}%"></div></div>
  `;
  tile.addEventListener('click', () => jumpToSwe(''));
  el.appendChild(tile);
}

// ---- Trend / health section (Overview page) --------------------------------
// All three charts are hand-rolled (SVG / flex bars) rather than pulled from a
// charting library, so dashboard.html stays a single self-contained file.

function renderLineChartSvg(xLabels, series, dataSets) {
  const W = 760, H = 220, padL = 40, padR = 16, padT = 16, padB = 28;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  let maxY = 1;
  dataSets.forEach(arr => arr.forEach(v => { if (v != null && v > maxY) maxY = v; }));
  maxY = Math.ceil(maxY * 1.15) || 1;
  const n = xLabels.length;
  const xFor = i => padL + (n === 1 ? plotW / 2 : (i / (n - 1)) * plotW);
  const yFor = v => padT + plotH - (v / maxY) * plotH;

  let gridSvg = '';
  const steps = 4;
  for (let s = 0; s <= steps; s++) {
    const v = Math.round(maxY * s / steps);
    const y = yFor(v);
    gridSvg += `<line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="var(--grid)" stroke-width="1"/>`;
    gridSvg += `<text x="${padL - 6}" y="${y + 4}" text-anchor="end" font-size="10" fill="var(--muted)">${v}</text>`;
  }
  let xLabelSvg = '';
  const labelEvery = Math.max(1, Math.ceil(n / 6));
  xLabels.forEach((d, i) => {
    if (i % labelEvery === 0 || i === n - 1) {
      xLabelSvg += `<text x="${xFor(i)}" y="${H - 8}" text-anchor="middle" font-size="10" fill="var(--muted)">${esc(d.slice(5))}</text>`;
    }
  });

  let linesSvg = '';
  series.forEach((s, si) => {
    const pts = dataSets[si];
    const coords = pts.map((v, i) => (v == null ? null : `${xFor(i)},${yFor(v)}`)).filter(Boolean);
    if (coords.length) {
      linesSvg += `<polyline points="${coords.join(' ')}" fill="none" stroke="${s.color}" stroke-width="2"/>`;
      pts.forEach((v, i) => { if (v != null) linesSvg += `<circle cx="${xFor(i)}" cy="${yFor(v)}" r="2.5" fill="${s.color}"/>`; });
    }
  });

  const legendSvg = series.map(s => `<span style="display:inline-flex; align-items:center; gap:6px; margin-right:16px; font-size:12px; color:var(--text-secondary);"><span style="width:10px; height:10px; border-radius:2px; background:${s.color}; display:inline-block;"></span>${esc(s.label)}</span>`).join('');

  return `
    <div style="margin-bottom:8px;">${legendSvg}</div>
    <svg viewBox="0 0 ${W} ${H}" style="width:100%; height:auto; max-width:${W}px;">
      ${gridSvg}${xLabelSvg}${linesSvg}
    </svg>
  `;
}

function renderTrendChart() {
  const wrap = document.getElementById('trendChartWrap');
  const caption = document.getElementById('trendCaption');
  const dates = Object.keys(HISTORY).sort();
  if (dates.length < 2) {
    caption.textContent = '';
    wrap.innerHTML = `<div class="empty-state">${esc(t('trend_insufficient_body'))}</div>`;
    return;
  }
  caption.textContent = t('trend_caption', dates[0], dates[dates.length - 1]);
  const series = [
    { key: 'swe2', label: 'SWE2', color: 'var(--series-cp)' },
    { key: 'swe3', label: 'SWE3', color: 'var(--series-aa)' },
    { key: 'swe5', label: 'SWE5', color: 'var(--series-ipod)' },
    { key: 'bugs', label: t('tab_bug'), color: 'var(--critical)' },
  ];
  const dataSets = series.map(s => dates.map(d => {
    const snap = HISTORY[d] && HISTORY[d][s.key];
    return snap ? (snap.total - snap.done) : null;
  }));
  wrap.innerHTML = renderLineChartSvg(dates, series, dataSets);
}

function renderAgingBars() {
  const el = document.getElementById('agingBars');
  const caption = document.getElementById('agingCaption');
  const notDone = [...DATA.filter(r => !r.done), ...BUGS.filter(r => !r.done)];
  const now = Date.now();
  const buckets = [
    { key: '0-7', label: t('aging_0_7'), min: 0, max: 7, color: 'var(--good)' },
    { key: '8-14', label: t('aging_8_14'), min: 8, max: 14, color: 'var(--warning)' },
    { key: '15-30', label: t('aging_15_30'), min: 15, max: 30, color: 'var(--serious)' },
    { key: '30+', label: t('aging_30_plus'), min: 31, max: Infinity, color: 'var(--critical)' },
  ];
  const counts = { '0-7': 0, '8-14': 0, '15-30': 0, '30+': 0 };
  let unknown = 0;
  notDone.forEach(r => {
    if (!r.created) { unknown++; return; }
    const days = Math.floor((now - new Date(r.created).getTime()) / 86400000);
    if (isNaN(days)) { unknown++; return; }
    const b = buckets.find(b => days >= b.min && days <= b.max) || buckets[buckets.length - 1];
    counts[b.key]++;
  });
  const total = notDone.length;
  caption.textContent = t('aging_caption', total, unknown);
  el.innerHTML = '';
  buckets.forEach(b => {
    const count = counts[b.key];
    const pct = total ? Math.round(count / total * 100) : 0;
    const div = document.createElement('div');
    div.className = 'bar-row';
    div.innerHTML = `
      <div class="name">${esc(b.label)}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.max(pct, 3)}%; background:${b.color}"><span>${pct}%</span></div></div>
      <div class="bar-count">${count}</div>
    `;
    el.appendChild(div);
  });
}

function isoWeekLabel(date) {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = (d.getUTCDay() + 6) % 7;
  d.setUTCDate(d.getUTCDate() - dayNum + 3);
  const firstThursday = new Date(Date.UTC(d.getUTCFullYear(), 0, 4));
  const weekNum = 1 + Math.round(((d - firstThursday) / 86400000 - 3 + ((firstThursday.getUTCDay() + 6) % 7)) / 7);
  return `${d.getUTCFullYear()}-W${String(weekNum).padStart(2, '0')}`;
}

function renderBugInflowChart() {
  const wrap = document.getElementById('bugInflowChartWrap');
  const caption = document.getElementById('bugInflowCaption');
  const withCreated = BUGS.filter(r => r.created);
  if (!withCreated.length) {
    caption.textContent = t('buginflow_no_data');
    wrap.innerHTML = '';
    return;
  }
  const counts = {};
  withCreated.forEach(r => {
    const wk = isoWeekLabel(new Date(r.created));
    counts[wk] = (counts[wk] || 0) + 1;
  });
  const weeks = Object.keys(counts).sort().slice(-12);
  caption.textContent = t('buginflow_caption', weeks[0], weeks[weeks.length - 1]);
  const maxV = Math.max(...weeks.map(w => counts[w]), 1);
  wrap.innerHTML = `
    <div style="display:flex; align-items:flex-end; gap:6px; height:160px; padding-top:8px;">
      ${weeks.map(w => {
        const v = counts[w];
        const h = Math.round((v / maxV) * 100);
        return `<div style="flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%;">
          <div style="font-size:11px; color:var(--text-secondary); margin-bottom:2px;">${v}</div>
          <div style="width:100%; max-width:28px; height:${Math.max(h, 3)}%; background:var(--series-aa); border-radius:3px 3px 0 0;"></div>
          <div style="font-size:9px; color:var(--muted); margin-top:4px;">${esc(w.slice(6))}</div>
        </div>`;
      }).join('')}
    </div>
  `;
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
    t('subfeature_caption', total, group.feature);
  const counts = {};
  notDone.forEach(r => { counts[r.subFeature] = (counts[r.subFeature] || 0) + 1; });
  const rows = Object.keys(counts)
    .map(name => ({ name: subFeatureDisplay(name), fullName: name, count: counts[name] }))
    .sort((a, b) => b.count - a.count);
  el.innerHTML = '';
  rows.forEach(row => {
    const pct = total ? Math.round(row.count / total * 100) : 0;
    const color = row.fullName === '未分類' ? 'var(--muted)' : group.color;
    const div = document.createElement('div');
    div.className = 'bar-row bar-row-pct bar-row-clickable';
    div.title = t('jump_tooltip', row.name);
    div.innerHTML = `
      <div class="name wide" title="${esc(row.name)}">${esc(row.name)}</div>
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
      <p class="caption">${esc(t('assignee_caption', total))}</p>
      <div class="bars-target"></div>
    `;
    const target = col.querySelector('.bars-target');
    rows.forEach(row => {
      const pct = total ? Math.round(row.count / total * 100) : 0;
      const div = document.createElement('div');
      div.className = 'bar-row bar-row-pct bar-row-clickable';
      div.title = t('jump_tooltip_plain', row.name);
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
  while (sel.options.length > 1) sel.remove(1);
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
      opt.textContent = subFeatureDisplay(full);
      optgroup.appendChild(opt);
    });
    sel.appendChild(optgroup);
  });
  const uncatOpt = document.createElement('option');
  uncatOpt.value = '未分類';
  uncatOpt.textContent = t('uncategorized');
  sel.appendChild(uncatOpt);
}

function populateMissingAssigneeFilter() {
  const sel = document.getElementById('missingAssigneeFilter');
  while (sel.options.length > 1) sel.remove(1);
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
  document.getElementById('missingCaption').textContent = t('missing_caption', rows.length, DATA.length);
  tbody.innerHTML = rows.length ? rows.map(r => `
    <tr>
      <td class="key"><a href="${ticketUrl(r.key)}" target="_blank">${r.key}</a></td>
      <td>${r.swe}</td>
      <td>${esc(r.feature)}</td>
      <td>${esc(subFeatureDisplay(r.subFeature))}</td>
      <td>${esc(r.assignee)}</td>
      <td>${statusBadge(r)}</td>
      <td>${esc(labelBucketText(r.labelBucket))}</td>
      <td>${esc(r.summary)}</td>
    </tr>
  `).join('') : `<tr><td colspan="8" class="empty-state">${esc(t('empty_state'))}</td></tr>`;
}

function renderBugPanel() {
  const panel = document.getElementById('panel-Bug');
  const done = BUGS.filter(r => r.done).length;
  const total = BUGS.length;
  const pct = total ? Math.round(done / total * 100) : 0;
  panel.innerHTML = `
    <div class="stat-row" id="bugPriorityTiles"></div>
    <section class="card">
      <h2>${esc(t('bug_subfeature_heading'))}</h2>
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
      <h2>${esc(t('bug_assignee_heading'))}</h2>
      <p class="caption">${esc(t('team_map_note'))}</p>
      <div id="bugAssigneeBarsContainer" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:24px;"></div>
    </section>
    <section class="card">
      <h2>${esc(t('bug_list_heading'))}</h2>
      <p class="caption" id="bugMissingCaption"></p>
      <div class="filters">
        <select id="bugFeatureFilter">
          <option value="">${esc(t('all_feature'))}</option>
          <option value="CarPlay">CarPlay</option>
          <option value="Android Auto">Android Auto</option>
          <option value="iPod">iPod</option>
        </select>
        <select id="bugStatusFilter">
          <option value="">${esc(t('all_status'))}</option>
          <option value="done">${esc(t('status_done'))}</option>
          <option value="not-done">${esc(t('status_not_done'))}</option>
        </select>
        <select id="bugLabelFilter">
          <option value="">${esc(t('all_label_bucket'))}</option>
          <option value="ASW-R2">ASW-R2</option>
          <option value="ASW-R3 (不含CPAA 0830)">${esc(t('label_bucket_asw_r3'))}</option>
          <option value="CPAA0830">CPAA0830</option>
          <option value="三者皆無">${esc(t('label_bucket_none'))}</option>
        </select>
        <select id="bugSubFeatureFilter">
          <option value="">${esc(t('all_subfeature'))}</option>
        </select>
        <select id="bugAssigneeFilter">
          <option value="">${esc(t('all_assignee'))}</option>
        </select>
        <select id="bugSeverityFilter">
          <option value="">${esc(t('all_severity'))}</option>
        </select>
        <select id="bugPriorityFilter">
          <option value="">${esc(t('all_priority'))}</option>
        </select>
        <input type="text" id="bugSearch" placeholder="${esc(t('search_placeholder'))}">
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th data-sort="key">Key</th><th data-sort="feature">${esc(t('th_feature'))}</th><th data-sort="subFeature">${esc(t('th_subfeature'))}</th>
            <th data-sort="assignee">${esc(t('th_assignee'))}</th><th data-sort="severity">${esc(t('th_severity'))}</th><th data-sort="priority">${esc(t('th_priority'))}</th><th data-sort="status">${esc(t('th_status'))}</th>
            <th data-sort="labelBucket">${esc(t('th_label_bucket'))}</th><th data-sort="summary">${esc(t('th_summary'))}</th>
          </tr></thead>
          <tbody id="bugTbody"></tbody>
        </table>
      </div>
    </section>
  `;

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
        opt.textContent = subFeatureDisplay(full);
        optgroup.appendChild(opt);
      });
      subFeatureSel.appendChild(optgroup);
    });
    const uncatOpt = document.createElement('option');
    uncatOpt.value = '未分類';
    uncatOpt.textContent = t('uncategorized');
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
    document.getElementById('bugMissingCaption').textContent = t('bug_missing_caption', rows.length);
    tbody.innerHTML = rows.length ? rows.map(r => `
      <tr>
        <td class="key"><a href="${ticketUrl(r.key)}" target="_blank">${r.key}</a></td>
        <td>${esc(r.feature)}</td>
        <td>${esc(subFeatureDisplay(r.subFeature))}</td>
        <td>${esc(r.assignee)}</td>
        <td>${esc(severityText(r.severity))}</td>
        <td>${esc(r.priority)}</td>
        <td>${bugStatusBadge(r)}</td>
        <td>${esc(labelBucketText(r.labelBucket))}</td>
        <td>${esc(r.summary)}</td>
      </tr>
    `).join('') : `<tr><td colspan="9" class="empty-state">${esc(t('empty_state'))}</td></tr>`;
  }
  [featureSel, statusSel, labelSel, subFeatureSel, assigneeSel, severitySel, prioritySel].forEach(el => el.addEventListener('change', renderBugTable));
  search.addEventListener('input', renderBugTable);
  attachSortHandlers(tbody.closest('table').querySelector('thead'), bugSortState, renderBugTable);
  renderBugTable();

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

  function renderBugPriorityTiles() {
    const el = document.getElementById('bugPriorityTiles');
    el.innerHTML = '';
    const makeTile = (label, subset, clickValue) => {
      const d = subset.filter(r => r.done).length;
      const total = subset.length;
      const notDone = total - d;
      const p = total ? Math.round(d / total * 100) : 0;
      const tile = document.createElement('div');
      tile.className = clickValue !== null ? 'stat-tile stat-tile-clickable' : 'stat-tile';
      tile.innerHTML = `
        <div class="label">${esc(label)}</div>
        <div class="value">${notDone}</div>
        <div class="sub">${esc(t('tile_sub', d, total, p))}</div>
        <div class="meter"><div style="width:${p}%"></div></div>
      `;
      if (clickValue !== null) tile.addEventListener('click', () => jumpToBugPriority(clickValue));
      el.appendChild(tile);
    };
    makeTile(t('bug_priority_bug_total'), BUGS, null);
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
        t('bug_subfeature_caption', total, group.feature);
      const counts = {};
      notDone.forEach(r => { counts[r.subFeature] = (counts[r.subFeature] || 0) + 1; });
      const rows = Object.keys(counts)
        .map(name => ({ name: subFeatureDisplay(name), fullName: name, count: counts[name] }))
        .sort((a, b) => b.count - a.count);
      el.innerHTML = '';
      rows.forEach(row => {
        const pct = total ? Math.round(row.count / total * 100) : 0;
        const color = row.fullName === '未分類' ? 'var(--muted)' : group.color;
        const div = document.createElement('div');
        div.className = 'bar-row bar-row-pct bar-row-clickable';
        div.title = t('jump_tooltip', row.name);
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
      const teamTotal = teamRows.length;
      const counts = {};
      teamRows.forEach(r => { counts[r.assignee] = (counts[r.assignee] || 0) + 1; });
      const rows = Object.keys(counts)
        .map(name => ({ name, count: counts[name] }))
        .sort((a, b) => b.count - a.count);

      const col = document.createElement('div');
      col.style.cssText = 'flex:1 1 260px; min-width:260px; max-width:100%; overflow:hidden;';
      col.innerHTML = `
        <h3 style="margin:0 0 4px; font-size:14px;">${esc(team)}</h3>
        <p class="caption">${esc(t('bug_assignee_caption', teamTotal))}</p>
        <div class="bars-target"></div>
      `;
      const target = col.querySelector('.bars-target');
      rows.forEach(row => {
        const pct2 = teamTotal ? Math.round(row.count / teamTotal * 100) : 0;
        const div = document.createElement('div');
        div.className = 'bar-row bar-row-pct bar-row-clickable';
        div.title = t('jump_tooltip_plain', row.name);
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
        <div class="label">${esc(t('audio_not_done_count'))}</div>
        <div class="value">${notDone}</div>
        <div class="sub">${esc(t('audio_pct_sub', pct, done, total))}</div>
        <div class="meter"><div style="width:${pct}%"></div></div>
      </div>
    </div>
    <section class="card">
      <h2>${esc(t('audio_group_heading'))}</h2>
      <p class="caption">${esc(t('audio_group_desc'))}</p>
      <div class="stat-row">
        ${groupRows.map(g => `
          <div class="stat-tile stat-tile-clickable" data-group="${esc(g.group)}">
            <div class="label">${g.group}</div>
            <div class="value">${g.notDone}</div>
            <div class="sub">${esc(t('audio_group_sub', g.notDone, g.total, g.done, g.total ? Math.round(g.done/g.total*100) : 0))}</div>
          </div>
        `).join('')}
      </div>
    </section>
    <section class="card">
      <h2>${esc(t('audio_list_heading'))}</h2>
      <p class="caption" id="audioCaption"></p>
      <div class="chip-row" id="audioAssigneeChips"></div>
      <div class="filters">
        <select id="audioGroupFilter">
          <option value="">${esc(t('all_group'))}</option>
          ${[...AUDIO_GROUPS, 'Other'].map(g => `<option value="${g}">${g}</option>`).join('')}
        </select>
        <input type="text" id="audioSearch" placeholder="${esc(t('search_placeholder'))}">
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th data-sort="key">Key</th><th data-sort="group">${esc(t('th_group'))}</th><th data-sort="issueType">${esc(t('th_issue_type'))}</th>
            <th data-sort="status">${esc(t('th_status'))}</th><th data-sort="assignee">${esc(t('th_assignee'))}</th><th data-sort="summary">${esc(t('th_summary'))}</th>
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
    const all = [{ name: '', label: t('audio_chip_all', AUDIO_NOT_DONE.length) }, ...assignees.map(a => ({ name: a, label: `${a} (${assigneeCounts[a]})` }))];
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
    document.getElementById('audioCaption').textContent = t('audio_caption', rows.length, AUDIO_NOT_DONE.length);

    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${esc(t('empty_state'))}</td></tr>`;
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
      return `<tr><td colspan="6" class="group-header">${esc(t('audio_group_header_row', a, grp.length))}</td></tr>` + grp.map(rowHtml).join('');
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
      <h2>${esc(t('pretest_list_heading'))}</h2>
      <p class="caption" id="pretestCaption"></p>
      <div class="filters">
        <select id="pretestGroupFilter">
          <option value="">${esc(t('all_group'))}</option>
          <option value="CP (Facet)">CP (Facet)</option>
          <option value="AA (PCTS)">AA (PCTS)</option>
        </select>
        <select id="pretestStatusFilter">
          <option value="">${esc(t('all_status'))}</option>
          <option value="done">${esc(t('status_done'))}</option>
          <option value="not-done">${esc(t('status_not_done'))}</option>
        </select>
        <select id="pretestSeverityFilter">
          <option value="">${esc(t('all_severity'))}</option>
        </select>
        <input type="text" id="pretestSearch" placeholder="${esc(t('search_placeholder'))}">
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th data-sort="key">Key</th><th data-sort="pretestGroup">${esc(t('th_group'))}</th><th data-sort="assignee">${esc(t('th_assignee'))}</th>
            <th data-sort="severity">${esc(t('th_severity'))}</th><th data-sort="status">${esc(t('th_status'))}</th><th data-sort="summary">${esc(t('th_summary'))}</th>
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
      const total = subset.length;
      const notDone = total - d;
      const p = total ? Math.round(d / total * 100) : 0;
      const tile = document.createElement('div');
      tile.className = 'stat-tile stat-tile-clickable';
      tile.innerHTML = `
        <div class="label">${esc(label)}</div>
        <div class="value">${notDone}</div>
        <div class="sub">${esc(t('tile_sub', d, total, p))}</div>
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
      opt.textContent = severityText(sev);
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
    document.getElementById('pretestCaption').textContent = t('pretest_caption', rows.length);
    tbody.innerHTML = rows.length ? rows.map(r => `
      <tr>
        <td class="key"><a href="${ticketUrl(r.key)}" target="_blank">${r.key}</a></td>
        <td>${esc(r.pretestGroup)}</td>
        <td>${esc(r.assignee)}</td>
        <td>${esc(severityText(r.severity))}</td>
        <td>${bugStatusBadge(r)}</td>
        <td>${esc(r.summary)}</td>
      </tr>
    `).join('') : `<tr><td colspan="6" class="empty-state">${esc(t('empty_state'))}</td></tr>`;
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

document.getElementById('langToggle').addEventListener('click', () => {
  LANG = LANG === 'zh' ? 'en' : 'zh';
  try { localStorage.setItem('cpaaDashboardLang', LANG); } catch (e) { /* localStorage unavailable */ }
  applyStaticI18n();
  renderCompletion();
  renderTrendChart();
  renderAgingBars();
  renderBugInflowChart();
  renderSubFeatureBars();
  renderAssigneeBars();
  populateMissingSubFeatureFilter();
  populateMissingAssigneeFilter();
  renderMissingTable();
  renderBugPanel();
  renderAudioPanel();
  renderPretestPanel();
});

applyStaticI18n();
renderCompletion();
renderTrendChart();
renderAgingBars();
renderBugInflowChart();
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

html = HTML_TEMPLATE.replace("__DATA_JSON__", DATA_JSON).replace("__UPDATED_AT__", UPDATED_AT)

with open("dashboard.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Wrote dashboard.html,", len(html), "bytes")
