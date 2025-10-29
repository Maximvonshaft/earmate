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

              main {
                flex: 1;
                padding: 2rem;
                display: grid;
                gap: 1.5rem;
              }

              .filters,
              .panels,
              .runs-section {
                background: #fff;
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
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

              .filters button {
                background: #1f6feb;
                color: #fff;
                border: none;
                padding: 0.5rem 1.25rem;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
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
              <p>洞察采集任务的运行节奏、指标趋势与日志详情。</p>
            </header>
            <main>
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
                };

                const state = {
                  dailyChart: null,
                  metricChart: null,
                  series: [],
                };

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

                elements.refreshButton.addEventListener('click', refresh);
                elements.ruleInput.addEventListener('keyup', (event) => {
                  if (event.key === 'Enter') {
                    refresh();
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

                refresh();
              });
            </script>
          </body>
        </html>
        """
    ).strip()
