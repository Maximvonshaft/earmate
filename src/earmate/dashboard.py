"""Static HTML template for the monitoring dashboard prototype."""

from __future__ import annotations

from textwrap import dedent


def render_dashboard_page() -> str:
    """Return the HTML markup for the monitoring dashboard prototype."""

    return dedent(
        """
        <!DOCTYPE html>
        <html lang=\"zh-CN\">
          <head>
            <meta charset=\"utf-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            <title>EarMate 监控仪表板</title>
            <link
              rel=\"stylesheet\"
              href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap\"
            />
            <style>
              :root {
                color-scheme: light dark;
                font-family: 'Inter', system-ui, -apple-system,
                  BlinkMacSystemFont, 'Segoe UI', sans-serif;
                line-height: 1.5;
                background-color: #f6f8fb;
              }

              body {
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
              }

              header {
                background: linear-gradient(120deg, #1f6feb, #794cff);
                color: #fff;
                padding: 1.5rem 2rem;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
              }

              header h1 {
                margin: 0;
                font-size: 1.75rem;
              }

              header p {
                margin: 0.5rem 0 0 0;
                opacity: 0.85;
              }

              main {
                flex: 1;
                padding: 2rem;
                display: grid;
                gap: 1.5rem;
                grid-template-columns: minmax(280px, 340px) 1fr;
                align-items: start;
              }

              .monitoring-column {
                display: grid;
                gap: 1.5rem;
              }

              .filters,
              .panels,
              .runs-section,
              .session-panel,
              .session-detail,
              .session-events {
                background: #fff;
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
              }

              .session-panel {
                display: flex;
                flex-direction: column;
                gap: 1rem;
              }

              .session-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 1rem;
              }

              .session-header h2 {
                margin: 0;
                font-size: 1.2rem;
              }

              .session-header button,
              .filters button,
              .session-rule button {
                background: #1f6feb;
                color: #fff;
                border: none;
                padding: 0.5rem 1.25rem;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
              }

              .session-description {
                margin: 0;
                font-size: 0.9rem;
                color: #475569;
              }

              .session-list {
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
                max-height: 320px;
                overflow-y: auto;
                padding-right: 0.25rem;
              }

              .session-card {
                border: 1px solid #d0d7ea;
                border-radius: 12px;
                padding: 0.75rem 1rem;
                text-align: left;
                background: #f8fafc;
                cursor: pointer;
                transition: border-color 0.2s ease, box-shadow 0.2s ease,
                  transform 0.2s ease;
              }

              .session-card:hover {
                border-color: #1f6feb;
                box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
                transform: translateY(-1px);
              }

              .session-card.is-active {
                border-color: #794cff;
                background: rgba(121, 76, 255, 0.08);
                box-shadow: 0 4px 16px rgba(121, 76, 255, 0.2);
              }

              .session-card h3 {
                margin: 0;
                font-size: 1rem;
              }

              .session-card p {
                margin: 0.35rem 0 0 0;
                font-size: 0.85rem;
                color: #475569;
              }

              .session-card footer {
                margin-top: 0.5rem;
                font-size: 0.75rem;
                color: #64748b;
              }

              .session-detail,
              .session-events {
                display: flex;
                flex-direction: column;
                gap: 1rem;
              }

              .session-detail h3 {
                margin: 0;
              }

              .session-detail-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 1rem;
              }

              .session-subtitle {
                margin: 0.25rem 0 0 0;
                color: #475569;
                font-size: 0.9rem;
              }

              .session-chip {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 0.25rem 0.75rem;
                border-radius: 999px;
                background: rgba(31, 111, 235, 0.12);
                color: #1f6feb;
                font-size: 0.75rem;
                font-weight: 600;
              }

              .session-meta {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 0.75rem;
              }

              .session-meta div {
                background: #f8fafc;
                border-radius: 12px;
                padding: 0.75rem;
                border: 1px solid #e2e8f0;
              }

              .session-meta span {
                display: block;
                font-size: 0.75rem;
                color: #64748b;
              }

              .session-meta strong {
                display: block;
                margin-top: 0.25rem;
                font-size: 0.9rem;
              }

              .session-analytics,
              .session-metadata,
              .session-selectors,
              .session-rule {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
              }

              .session-metadata ul,
              .session-selectors ul {
                list-style: none;
                margin: 0;
                padding: 0;
                display: grid;
                gap: 0.35rem;
              }

              .session-metadata li,
              .session-selectors li {
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: #f8fafc;
                border-radius: 12px;
                padding: 0.6rem 0.75rem;
                border: 1px solid #e2e8f0;
                font-size: 0.85rem;
              }

              .session-metadata strong,
              .session-selectors strong {
                font-weight: 600;
                color: #1f2937;
              }

              .session-analytics-badges {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
              }

              .session-events ol {
                margin: 0;
                padding-left: 0;
                list-style: none;
                display: grid;
                gap: 0.75rem;
                max-height: 320px;
                overflow-y: auto;
              }

              .session-event-item {
                display: grid;
                grid-template-columns: auto 1fr;
                gap: 0.75rem;
                align-items: start;
                background: #f8fafc;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 0.75rem;
              }

              .session-event-index {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: rgba(121, 76, 255, 0.12);
                color: #794cff;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 0.9rem;
              }

              .session-event-body strong {
                display: block;
                font-size: 0.9rem;
              }

              .session-event-body time {
                font-size: 0.75rem;
                color: #64748b;
              }

              .session-event-summary {
                margin: 0.35rem 0 0 0;
                font-size: 0.85rem;
                color: #475569;
                white-space: pre-wrap;
              }

              .filters {
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
                align-items: center;
              }

              .filters label {
                font-weight: 600;
              }

              .filters input {
                padding: 0.5rem 0.75rem;
                border-radius: 8px;
                border: 1px solid #cbd5f5;
                min-width: 240px;
              }

              .panel-filters {
                padding: 0;
                background: transparent;
                box-shadow: none;
              }

              .summary-cards {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 1rem;
              }

              .summary-card {
                background: #f8fafc;
                border-radius: 12px;
                padding: 1rem;
                border: 1px solid #e2e8f0;
              }

              .summary-card h3 {
                margin: 0 0 0.5rem 0;
                font-size: 0.95rem;
                color: #475569;
              }

              .summary-card strong {
                font-size: 1.5rem;
                color: #0f172a;
              }

              .panels {
                display: grid;
                gap: 2rem;
              }

              .panel-title {
                font-weight: 600;
                margin-bottom: 0.75rem;
              }

              .runs-wrapper {
                display: grid;
                grid-template-columns: minmax(0, 1fr) minmax(0, 320px);
                gap: 1.5rem;
              }

              table {
                width: 100%;
                border-collapse: collapse;
                font-size: 0.9rem;
              }

              th,
              td {
                padding: 0.5rem 0.75rem;
                border-bottom: 1px solid #e2e8f0;
                text-align: left;
                vertical-align: top;
              }

              tr:hover {
                background: rgba(31, 111, 235, 0.08);
                cursor: pointer;
              }

              .run-detail {
                background: #f8fafc;
                border-radius: 12px;
                padding: 1rem;
                border: 1px solid #e2e8f0;
                font-size: 0.85rem;
                white-space: pre-wrap;
                overflow: auto;
                max-height: 400px;
              }

              .empty-state {
                color: #64748b;
                font-size: 0.9rem;
              }

              @media (max-width: 1120px) {
                main {
                  grid-template-columns: 1fr;
                }

                .monitoring-column {
                  order: 2;
                }

                .session-panel {
                  order: 1;
                }
              }

              @media (max-width: 960px) {
                .runs-wrapper {
                  grid-template-columns: 1fr;
                }
              }
            </style>
            <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
          </head>
          <body>
            <header>
              <h1>EarMate 监控仪表板</h1>
              <p>串联录制工作流与调度监控，完成从采集设计到执行追踪的闭环。</p>
            </header>
            <main>
              <section class=\"session-panel\">
                <div class=\"session-header\">
                  <div>
                    <h2>录制会话工作台</h2>
                    <p class=\"session-description\">
                      查看录制输出、快速跳转至关联规则并串联调度数据。
                    </p>
                  </div>
                  <button id=\"sessions-refresh\" type=\"button\">刷新会话</button>
                </div>
                <div id=\"session-list\" class=\"session-list\"></div>
                <p id=\"sessions-empty\" class=\"empty-state\">
                  暂无录制会话，启动浏览器录制后将自动出现。
                </p>
                <section id=\"session-detail\" class=\"session-detail\">
                  <p class=\"empty-state\">选择会话以查看配置、元数据与关联规则。</p>
                </section>
                <section id=\"session-events\" class=\"session-events\">
                  <p class=\"empty-state\">选择会话后可查看事件回放轨迹。</p>
                </section>
              </section>

              <div class=\"monitoring-column\">
                <section class=\"filters\">
                  <label for=\"rule-filter\">按规则筛选：</label>
                  <input id=\"rule-filter\" type=\"text\" placeholder=\"输入规则 ID（可选）\" />
                  <button id=\"refresh-btn\" type=\"button\">刷新数据</button>
                  <span id=\"last-updated\" class=\"empty-state\"></span>
                </section>

                <section class=\"panels\">
                  <div>
                    <h2 class=\"panel-title\">执行概览</h2>
                    <div class=\"summary-cards\">
                      <div class=\"summary-card\">
                        <h3>累计执行</h3>
                        <strong id=\"summary-total\">-</strong>
                      </div>
                      <div class=\"summary-card\">
                        <h3>成功</h3>
                        <strong id=\"summary-succeeded\">-</strong>
                      </div>
                      <div class=\"summary-card\">
                        <h3>失败</h3>
                        <strong id=\"summary-failed\">-</strong>
                      </div>
                      <div class=\"summary-card\">
                        <h3>运行中</h3>
                        <strong id=\"summary-running\">-</strong>
                      </div>
                      <div class=\"summary-card\">
                        <h3>待执行</h3>
                        <strong id=\"summary-pending\">-</strong>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h2 class=\"panel-title\">日维度趋势</h2>
                    <canvas id=\"daily-chart\" height=\"160\"></canvas>
                    <p id=\"daily-empty\" class=\"empty-state\" hidden>暂无每日聚合数据。</p>
                  </div>

                  <div>
                    <h2 class=\"panel-title\">指标序列</h2>
                    <div class=\"filters panel-filters\">
                      <label for=\"metric-select\">选择指标：</label>
                      <select id=\"metric-select\"></select>
                    </div>
                    <canvas id=\"metric-chart\" height=\"160\"></canvas>
                    <p id=\"metric-empty\" class=\"empty-state\">暂无指标数据。</p>
                  </div>
                </section>

                <section class=\"runs-section\">
                  <h2 class=\"panel-title\">执行记录与日志</h2>
                  <div class=\"runs-wrapper\">
                    <div>
                      <table>
                        <thead>
                          <tr>
                            <th>执行 ID</th>
                            <th>状态</th>
                            <th>开始时间</th>
                            <th>耗时(ms)</th>
                          </tr>
                        </thead>
                        <tbody id=\"runs-table\"></tbody>
                      </table>
                      <p id=\"runs-empty\" class=\"empty-state\">暂无执行记录。</p>
                    </div>
                    <aside>
                      <h3 style=\"margin-top: 0;\">日志详情</h3>
                      <div id=\"run-detail\" class=\"run-detail\">选择一条执行记录查看日志</div>
                    </aside>
                  </div>
                </section>
              </div>
            </main>
            <script>
              window.addEventListener('DOMContentLoaded', () => {
                const elements = {
                  ruleInput: document.getElementById('rule-filter'),
                  refreshButton: document.getElementById('refresh-btn'),
                  lastUpdated: document.getElementById('last-updated'),
                  runsTable: document.getElementById('runs-table'),
                  runsEmpty: document.getElementById('runs-empty'),
                  runDetail: document.getElementById('run-detail'),
                  dailyEmpty: document.getElementById('daily-empty'),
                  metricSelect: document.getElementById('metric-select'),
                  metricEmpty: document.getElementById('metric-empty'),
                  sessionsRefresh: document.getElementById('sessions-refresh'),
                  sessionsList: document.getElementById('session-list'),
                  sessionsEmpty: document.getElementById('sessions-empty'),
                  sessionDetail: document.getElementById('session-detail'),
                  sessionEvents: document.getElementById('session-events'),
                };

                const defaultSessionDetail =
                  '<p class="empty-state">选择会话以查看配置、元数据与关联规则。</p>';
                const defaultSessionEvents =
                  '<p class="empty-state">选择会话后可查看事件回放轨迹。</p>';

                const state = {
                  dailyChart: null,
                  metricChart: null,
                  series: [],
                  sessions: [],
                  selectedSessionId: null,
                  sessionRuleMap: {},
                };

                function escapeHtml(value) {
                  return String(value)
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#39;');
                }

                function formatDate(value) {
                  if (!value) {
                    return '-';
                  }
                  const date = new Date(value);
                  if (Number.isNaN(date.getTime())) {
                    return value;
                  }
                  return date.toLocaleString();
                }

                function formatDuration(value) {
                  if (value === null || value === undefined) {
                    return '-';
                  }
                  return Math.round(value);
                }

                function formatRelative(value) {
                  if (!value) {
                    return '-';
                  }
                  const date = new Date(value);
                  const timestamp = date.getTime();
                  if (Number.isNaN(timestamp)) {
                    return '-';
                  }
                  const diff = Date.now() - timestamp;
                  if (Number.isNaN(diff)) {
                    return '-';
                  }
                  if (diff <= 0) {
                    return '刚刚';
                  }
                  const minutes = Math.round(diff / 60000);
                  if (minutes < 1) {
                    return '刚刚';
                  }
                  if (minutes < 60) {
                    return `${minutes} 分钟前`;
                  }
                  const hours = Math.round(minutes / 60);
                  if (hours < 24) {
                    return `${hours} 小时前`;
                  }
                  const days = Math.round(hours / 24);
                  return `${days} 天前`;
                }

                async function fetchJSON(url) {
                  const response = await fetch(url);
                  if (!response.ok) {
                    throw new Error(`请求失败: ${response.status}`);
                  }
                  return response.json();
                }

                function renderSummary(summary) {
                  const totals = summary?.by_status || {};
                  document.getElementById('summary-total').textContent = summary?.total ?? '-';
                  document.getElementById('summary-succeeded').textContent =
                    totals.succeeded ?? '-';
                  document.getElementById('summary-failed').textContent =
                    totals.failed ?? '-';
                  document.getElementById('summary-running').textContent =
                    totals.running ?? '-';
                  document.getElementById('summary-pending').textContent =
                    totals.pending ?? '-';
                }

                function renderDaily(daily) {
                  if (!daily || daily.length === 0) {
                    elements.dailyEmpty.hidden = false;
                    if (state.dailyChart) {
                      state.dailyChart.destroy();
                      state.dailyChart = null;
                    }
                    const canvas = document.getElementById('daily-chart');
                    const ctx = canvas.getContext('2d');
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    return;
                  }
                  elements.dailyEmpty.hidden = true;
                  const labels = daily.map((item) => item.date);
                  const statuses = ['succeeded', 'failed', 'running', 'pending'];
                  const colors = {
                    succeeded: '#16a34a',
                    failed: '#dc2626',
                    running: '#1f6feb',
                    pending: '#f59e0b',
                  };
                  const datasets = statuses.map((status) => ({
                    label: status,
                    data: daily.map((item) => item.by_status?.[status] ?? 0),
                    borderColor: colors[status],
                    backgroundColor: colors[status],
                    tension: 0.3,
                  }));
                  const ctx = document.getElementById('daily-chart').getContext('2d');
                  if (state.dailyChart) {
                    state.dailyChart.data.labels = labels;
                    state.dailyChart.data.datasets = datasets;
                    state.dailyChart.update();
                  } else {
                    state.dailyChart = new Chart(ctx, {
                      type: 'line',
                      data: { labels, datasets },
                      options: {
                        responsive: true,
                        plugins: {
                          legend: { position: 'top' },
                        },
                        scales: {
                          y: { beginAtZero: true, precision: 0 },
                        },
                      },
                    });
                  }
                }

                function renderMetricOptions(series) {
                  elements.metricSelect.innerHTML = '';
                  state.series = series || [];
                  if (!state.series.length) {
                    elements.metricEmpty.hidden = false;
                    const option = document.createElement('option');
                    option.textContent = '无可用指标';
                    option.value = '';
                    elements.metricSelect.append(option);
                    elements.metricSelect.disabled = true;
                    renderMetricSeries(null);
                    return;
                  }
                  elements.metricEmpty.hidden = true;
                  elements.metricSelect.disabled = false;
                  state.series.forEach((item, index) => {
                    const option = document.createElement('option');
                    option.textContent = item.name;
                    option.value = String(index);
                    elements.metricSelect.append(option);
                  });
                  elements.metricSelect.value = '0';
                  renderMetricSeries(0);
                }

                function renderMetricSeries(index) {
                  const canvas = document.getElementById('metric-chart');
                  const ctx = canvas.getContext('2d');
                  if (index === null || index === undefined || Number.isNaN(Number(index))) {
                    if (state.metricChart) {
                      state.metricChart.destroy();
                      state.metricChart = null;
                    }
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    elements.metricEmpty.hidden = false;
                    return;
                  }
                  const series = state.series[Number(index)];
                  if (!series || !series.points || !series.points.length) {
                    if (state.metricChart) {
                      state.metricChart.destroy();
                      state.metricChart = null;
                    }
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    elements.metricEmpty.hidden = false;
                    return;
                  }
                  const labels = series.points.map((point) => point.timestamp);
                  const data = series.points.map((point) => point.value);
                  elements.metricEmpty.hidden = true;
                  if (state.metricChart) {
                    state.metricChart.data.labels = labels;
                    state.metricChart.data.datasets = [
                      {
                        label: series.name,
                        data,
                        borderColor: '#794cff',
                        backgroundColor: 'rgba(121, 76, 255, 0.25)',
                        tension: 0.3,
                      },
                    ];
                    state.metricChart.update();
                  } else {
                    state.metricChart = new Chart(ctx, {
                      type: 'line',
                      data: {
                        labels,
                        datasets: [
                          {
                            label: series.name,
                            data,
                            borderColor: '#794cff',
                            backgroundColor: 'rgba(121, 76, 255, 0.25)',
                            tension: 0.3,
                          },
                        ],
                      },
                      options: {
                        responsive: true,
                        plugins: { legend: { display: false } },
                        scales: { y: { beginAtZero: true } },
                      },
                    });
                  }
                }

                function renderRuns(runs) {
                  elements.runsTable.innerHTML = '';
                  if (!runs || !runs.length) {
                    elements.runsEmpty.hidden = false;
                    return;
                  }
                  elements.runsEmpty.hidden = true;
                  const fragment = document.createDocumentFragment();
                  runs.forEach((run) => {
                    const row = document.createElement('tr');
                    row.dataset.runId = run.id;
                    row.innerHTML = `
                      <td>${run.id}</td>
                      <td>${run.status}</td>
                      <td>${formatDate(run.started_at || run.created_at)}</td>
                      <td>${formatDuration(run.duration_ms)}</td>
                    `;
                    fragment.append(row);
                  });
                  elements.runsTable.append(fragment);
                }

                function getSelectedSession() {
                  if (!state.selectedSessionId) {
                    return null;
                  }
                  return (
                    state.sessions.find((session) => session.id === state.selectedSessionId) || null
                  );
                }

                function summariseEvent(event) {
                  const payload = event.payload || {};
                  if (event.type === 'navigate' && payload.url) {
                    return `访问 ${escapeHtml(payload.url)}`;
                  }
                  if (event.type === 'capture_selector' && payload.role && payload.selector) {
                    return `捕获 ${escapeHtml(payload.role)} → ${escapeHtml(payload.selector)}`;
                  }
                  if (event.type === 'capture_detail_field' && payload.name && payload.selector) {
                    return `配置详情字段 ${escapeHtml(payload.name)} → ${escapeHtml(
                      payload.selector,
                    )}`;
                  }
                  if (event.type === 'set_pagination' && payload.type) {
                    const selector = payload.selector
                      ? ` · 选择器 ${escapeHtml(payload.selector)}`
                      : '';
                    return `设置翻页 ${escapeHtml(payload.type)}${selector}`;
                  }
                  if (event.type === 'add_action' && payload.type) {
                    const target = payload.selector ? ` · ${escapeHtml(payload.selector)}` : '';
                    return `新增动作 ${escapeHtml(payload.type)}${target}`;
                  }
                  if (event.type === 'set_metadata' && payload.key) {
                    return `记录元数据 ${escapeHtml(payload.key)} = ${escapeHtml(
                      payload.value ?? '',
                    )}`;
                  }
                  if (Object.keys(payload).length === 0) {
                    return '无附加信息';
                  }
                  return Object.entries(payload)
                    .map(([key, value]) => `${escapeHtml(key)}: ${escapeHtml(value)}`)
                    .join('，');
                }

                function renderSessionDetail(session) {
                  if (!session) {
                    elements.sessionDetail.innerHTML = defaultSessionDetail;
                    return;
                  }
                  const name = session.name ? escapeHtml(session.name) : '未命名会话';
                  const escapedEntry = session.entry ? escapeHtml(session.entry) : null;
                  const entry = escapedEntry
                    ? `<a href="${escapedEntry}" target="_blank" rel="noopener">${escapedEntry}</a>`
                    : '尚未设置入口 URL';
                  const analytics = session.analytics || {};
                  const typeBadges = Object.entries(analytics.types || {}).map(
                    ([type, count]) =>
                      `<span class="session-chip">${escapeHtml(type)} × ${escapeHtml(
                        count,
                      )}</span>`,
                  );
                  const metadataEntries = Object.entries(session.metadata || {});
                  const selectorsEntries = Object.entries(session.selectors || {});
                  const rule = state.sessionRuleMap[session.id];
                  const metadataHtml = metadataEntries.length
                    ? `<ul>${metadataEntries
                        .map(
                          ([key, value]) =>
                            `<li><span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong></li>`,
                        )
                        .join('')}</ul>`
                    : '<p class="empty-state">暂无自定义元数据。</p>';
                  const selectorsHtml = selectorsEntries.length
                    ? `<ul>${selectorsEntries
                        .map(
                          ([role, selector]) =>
                            `<li><span>${escapeHtml(role)}</span><strong>${escapeHtml(selector)}</strong></li>`,
                        )
                        .join('')}</ul>`
                    : '<p class="empty-state">尚未捕获列表字段。</p>';
                  const analyticsBadges =
                    typeBadges.length
                      ? typeBadges.join('')
                      : '<span class="empty-state">暂无操作统计。</span>';
                  let ruleHtml =
                    '<p class="empty-state">暂无关联规则，可通过发布接口一键生成。</p>';
                  if (rule) {
                    const ruleName = rule.rule?.name ? escapeHtml(rule.rule.name) : '未命名规则';
                    const status = rule.enabled ? '已启用' : '未启用';
                    ruleHtml = `
                      <div>
                        <p style="margin: 0 0 0.5rem 0;">
                          <strong>${ruleName}</strong>
                          <br />规则 ID：<code>${escapeHtml(rule.id)}</code>
                        </p>
                        <p style="margin: 0 0 0.75rem 0; color: #475569;">状态：${status}</p>
                        <button type="button" data-action="apply-rule" data-rule-id="${escapeHtml(
                          rule.id,
                        )}">在监控中查看</button>
                      </div>
                    `;
                  }
                  const analyticsDuration =
                    analytics.duration_seconds !== undefined
                      ? `${Math.round(analytics.duration_seconds)} 秒`
                      : '-';
                  const analyticsCount = analytics.count ?? session.event_count;
                  elements.sessionDetail.innerHTML = `
                    <header class="session-detail-header">
                      <div>
                        <h3>${name}</h3>
                        <p class="session-subtitle">${entry}</p>
                      </div>
                      <span class="session-chip">事件 ${escapeHtml(session.event_count)}</span>
                    </header>
                    <div class="session-meta">
                      <div>
                        <span>创建时间</span>
                        <strong>${formatDate(session.created_at)}</strong>
                      </div>
                      <div>
                        <span>最近更新</span>
                        <strong>${formatDate(session.updated_at)}</strong>
                      </div>
                      <div>
                        <span>相对时间</span>
                        <strong>${formatRelative(session.updated_at)}</strong>
                      </div>
                      <div>
                        <span>记录总数</span>
                        <strong>${escapeHtml(analyticsCount ?? '-')}</strong>
                      </div>
                      <div>
                        <span>会话耗时</span>
                        <strong>${analyticsDuration}</strong>
                      </div>
                    </div>
                    <section class="session-analytics">
                      <h4 style="margin: 0;">事件分布</h4>
                      <div class="session-analytics-badges">${analyticsBadges}</div>
                    </section>
                    <section class="session-metadata">
                      <h4 style="margin: 0;">会话元数据</h4>
                      ${metadataHtml}
                    </section>
                    <section class="session-selectors">
                      <h4 style="margin: 0;">列表选择器</h4>
                      ${selectorsHtml}
                    </section>
                    <section class="session-rule">
                      <h4 style="margin: 0;">关联规则</h4>
                      ${ruleHtml}
                    </section>
                  `;
                }

                function renderSessionEvents(session) {
                  if (!session) {
                    elements.sessionEvents.innerHTML = defaultSessionEvents;
                    return;
                  }
                  const events = session.events || [];
                  if (!events.length) {
                    elements.sessionEvents.innerHTML =
                      '<p class="empty-state">暂无事件，请继续在录制端操作。</p>';
                    return;
                  }
                  const items = events
                    .map(
                      (event, index) => `
                        <li class="session-event-item">
                          <span class="session-event-index">${index + 1}</span>
                          <div class="session-event-body">
                            <strong>${escapeHtml(event.type)}</strong>
                            <time>${formatDate(event.timestamp)}</time>
                            <p class="session-event-summary">${summariseEvent(event)}</p>
                          </div>
                        </li>
                      `,
                    )
                    .join('');
                  elements.sessionEvents.innerHTML = `
                    <h3 style="margin: 0;">事件回放</h3>
                    <ol>${items}</ol>
                  `;
                }

                async function loadDashboard(ruleId) {
                  const query = ruleId ? `?rule_id=${encodeURIComponent(ruleId)}` : '';
                  const dashboard = await fetchJSON(`/monitoring/dashboard${query}`);
                  renderSummary(dashboard.summary || {});
                  renderDaily(dashboard.daily || []);
                  renderMetricOptions(dashboard.series || []);
                }

                async function loadRuns(ruleId) {
                  const query = ruleId ? `?rule_id=${encodeURIComponent(ruleId)}` : '';
                  const runs = await fetchJSON(`/monitoring/runs${query}`);
                  renderRuns(runs.items || []);
                }

                async function refresh() {
                  const ruleId = elements.ruleInput.value.trim();
                  try {
                    await Promise.all([loadDashboard(ruleId), loadRuns(ruleId)]);
                    const now = new Date();
                    elements.lastUpdated.textContent = `最新刷新：${now.toLocaleString()}`;
                  } catch (error) {
                    console.error(error);
                    elements.lastUpdated.textContent = '数据加载失败，请稍后重试。';
                  }
                }

                async function loadSessions() {
                  elements.sessionsEmpty.textContent = '暂无录制会话，启动浏览器录制后将自动出现。';
                  elements.sessionsRefresh.disabled = true;
                  try {
                    const [sessionsPayload, rulesPayload] = await Promise.all([
                      fetchJSON('/recorder/sessions'),
                      fetchJSON('/rules'),
                    ]);
                    state.sessions = sessionsPayload.items || [];
                    state.sessionRuleMap = {};
                    (rulesPayload.items || []).forEach((rule) => {
                      const metadata = rule.rule?.metadata || {};
                      if (metadata.recorder_session) {
                        state.sessionRuleMap[metadata.recorder_session] = rule;
                      }
                    });
                    if (
                      state.selectedSessionId &&
                      !state.sessions.some((session) => session.id === state.selectedSessionId)
                    ) {
                      state.selectedSessionId = null;
                    }
                    if (!state.selectedSessionId && state.sessions.length) {
                      state.selectedSessionId = state.sessions[0].id;
                    }
                    renderSessions();
                    const selectedSession = getSelectedSession();
                    renderSessionDetail(selectedSession);
                    renderSessionEvents(selectedSession);
                    elements.sessionsEmpty.hidden = state.sessions.length > 0;
                  } catch (error) {
                    console.error(error);
                    elements.sessionsEmpty.hidden = false;
                    elements.sessionsEmpty.textContent = '会话加载失败，请稍后重试。';
                    state.sessions = [];
                    state.selectedSessionId = null;
                    renderSessions();
                    elements.sessionDetail.innerHTML =
                      '<p class="empty-state">会话数据加载失败，请检查服务状态。</p>';
                    elements.sessionEvents.innerHTML = defaultSessionEvents;
                  } finally {
                    elements.sessionsRefresh.disabled = false;
                  }
                }

                function renderSessions() {
                  elements.sessionsList.innerHTML = '';
                  if (!state.sessions.length) {
                    return;
                  }
                  const fragment = document.createDocumentFragment();
                  state.sessions.forEach((session) => {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.dataset.sessionId = session.id;
                    button.className = 'session-card';
                    if (state.selectedSessionId === session.id) {
                      button.classList.add('is-active');
                    }
                    const title = document.createElement('h3');
                    title.textContent = session.name || '未命名会话';
                    const entry = document.createElement('p');
                    entry.textContent = session.entry || '尚未设置入口 URL';
                    const footer = document.createElement('footer');
                    const footerParts = [
                      `更新 ${formatRelative(session.updated_at)}`,
                      `事件 ${session.event_count}`,
                    ];
                    footer.textContent = footerParts.join(' · ');
                    button.append(title, entry, footer);
                    fragment.append(button);
                  });
                  elements.sessionsList.append(fragment);
                }

                elements.refreshButton.addEventListener('click', () => {
                  refresh().catch((error) => console.error(error));
                });

                elements.ruleInput.addEventListener('keyup', (event) => {
                  if (event.key === 'Enter') {
                    refresh().catch((error) => console.error(error));
                  }
                });

                elements.metricSelect.addEventListener('change', (event) => {
                  const { value } = event.target;
                  if (value === '') {
                    renderMetricSeries(null);
                  } else {
                    renderMetricSeries(Number.parseInt(value, 10));
                  }
                });

                elements.runsTable.addEventListener('click', async (event) => {
                  const row = event.target.closest('tr[data-run-id]');
                  if (!row) {
                    return;
                  }
                  const runId = row.dataset.runId;
                  try {
                    const detail = await fetchJSON(`/monitoring/runs/${runId}`);
                    const lines = [];
                    lines.push(`执行 ID: ${detail.id}`);
                    lines.push(`规则 ID: ${detail.rule_id}`);
                    lines.push(`状态: ${detail.status}`);
                    lines.push(`开始时间: ${formatDate(detail.started_at || detail.created_at)}`);
                    lines.push(`结束时间: ${formatDate(detail.finished_at || detail.updated_at)}`);
                    lines.push(`耗时(ms): ${formatDuration(detail.duration_ms)}`);
                    if (detail.metrics && Object.keys(detail.metrics).length) {
                      lines.push('指标:');
                      Object.entries(detail.metrics).forEach(([key, value]) => {
                        lines.push(`  - ${key}: ${value}`);
                      });
                    }
                    if (detail.error_message) {
                      lines.push(`错误信息: ${detail.error_message}`);
                    }
                    if (detail.logs && detail.logs.length) {
                      lines.push('\n日志:');
                      detail.logs.forEach((entry) => {
                        lines.push(
                          `  [${entry.level}] ${formatDate(entry.timestamp)} - ${entry.message}`,
                        );
                      });
                    } else {
                      lines.push('\n日志: 暂无日志记录');
                    }
                    elements.runDetail.textContent = lines.join('\n');
                  } catch (error) {
                    console.error(error);
                    elements.runDetail.textContent = '日志加载失败，请稍后重试。';
                  }
                });

                elements.sessionsRefresh.addEventListener('click', () => {
                  loadSessions().catch((error) => console.error(error));
                });

                elements.sessionsList.addEventListener('click', (event) => {
                  const card = event.target.closest('button[data-session-id]');
                  if (!card) {
                    return;
                  }
                  state.selectedSessionId = card.dataset.sessionId;
                  renderSessions();
                  const session = getSelectedSession();
                  renderSessionDetail(session);
                  renderSessionEvents(session);
                });

                elements.sessionDetail.addEventListener('click', (event) => {
                  const target = event.target.closest('[data-action="apply-rule"]');
                  if (!target) {
                    return;
                  }
                  const ruleId = target.getAttribute('data-rule-id');
                  if (!ruleId) {
                    return;
                  }
                  elements.ruleInput.value = ruleId;
                  refresh().catch((error) => console.error(error));
                  target.textContent = '已应用';
                  setTimeout(() => {
                    target.textContent = '在监控中查看';
                  }, 1500);
                });

                loadSessions().catch((error) => console.error(error));
                refresh().catch((error) => console.error(error));
              });
            </script>
          </body>
        </html>
        """
    ).strip()
