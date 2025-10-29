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
                display: grid;
                gap: 1rem;
              }

              .header-top {
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
                justify-content: space-between;
                align-items: flex-start;
              }

              header h1 {
                margin: 0;
                font-size: 1.75rem;
              }

              .header-top p {
                margin: 0.25rem 0 0;
                max-width: 46rem;
              }

              .view-switch {
                display: inline-flex;
                background-color: rgba(255, 255, 255, 0.12);
                padding: 0.25rem;
                border-radius: 999px;
                gap: 0.25rem;
              }

              .view-switch button {
                background: transparent;
                border: none;
                color: inherit;
                padding: 0.35rem 1rem;
                border-radius: 999px;
                font-weight: 600;
                cursor: pointer;
                transition: background-color 0.2s ease;
              }

              .view-switch button.active,
              .view-switch button:hover {
                background-color: rgba(255, 255, 255, 0.2);
              }

              .header-controls {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem 1rem;
                align-items: center;
              }

              .header-controls label {
                font-weight: 600;
              }

              .header-controls input {
                padding: 0.45rem 0.75rem;
                border-radius: 8px;
                border: none;
                min-width: 240px;
              }

              main {
                flex: 1;
                padding: 2rem;
                display: grid;
                gap: 1.5rem;
              }

              .view {
                display: none;
              }

              .view.active {
                display: grid;
                gap: 1.5rem;
              }

              .card {
                background: #fff;
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
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

              .filters button,
              .primary-button {
                background: #1f6feb;
                color: #fff;
                border: none;
                padding: 0.5rem 1.25rem;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
              }

              .secondary-button {
                background: #e2e8f0;
                color: #0f172a;
                border: none;
                padding: 0.5rem 1.25rem;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
              }

              .secondary-button:hover {
                background: #cbd5f5;
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
                overflow: auto;
                max-height: 400px;
                display: grid;
                gap: 0.75rem;
              }

              .run-detail pre {
                margin: 0;
                white-space: pre-wrap;
                font-family: 'JetBrains Mono', 'Fira Code', 'SFMono-Regular', monospace;
              }

              .run-detail-actions {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
              }

              .link-button {
                background: transparent;
                border: none;
                color: #1f6feb;
                cursor: pointer;
                font-weight: 600;
                padding: 0;
              }

              .link-button:hover {
                text-decoration: underline;
              }

              .empty-state {
                color: #64748b;
                font-size: 0.9rem;
              }

              .status-message {
                font-size: 0.85rem;
              }

              .status-message.error {
                color: #f87171;
              }

              .recorder-layout {
                display: grid;
                grid-template-columns: minmax(0, 320px) minmax(0, 1fr);
                gap: 1.5rem;
              }

              .recorder-sidebar {
                display: grid;
                gap: 1rem;
              }

              .recorder-sessions {
                list-style: none;
                margin: 0;
                padding: 0;
                display: grid;
                gap: 0.75rem;
              }

              .recorder-session {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 0.75rem;
                cursor: pointer;
                transition: border-color 0.2s ease, box-shadow 0.2s ease;
              }

              .recorder-session.active,
              .recorder-session:hover {
                border-color: #1f6feb;
                box-shadow: 0 2px 6px rgba(31, 111, 235, 0.12);
              }

              .recorder-session h3 {
                margin: 0 0 0.25rem 0;
                font-size: 1rem;
                color: #0f172a;
              }

              .recorder-session small {
                color: #64748b;
              }

              .recorder-detail {
                background: #fff;
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
                display: grid;
                gap: 1rem;
              }

              .recorder-summary {
                background: #f8fafc;
                border-radius: 12px;
                padding: 1rem;
                border: 1px solid #e2e8f0;
                white-space: pre-wrap;
                font-family: 'JetBrains Mono', 'Fira Code', 'SFMono-Regular', monospace;
              }

              .recorder-events {
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 1rem;
                background: #f8fafc;
                max-height: 320px;
                overflow: auto;
              }

              .recorder-operations {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 1rem;
                display: grid;
                gap: 1rem;
              }

              .recorder-actions-grid {
                display: grid;
                gap: 0.75rem;
              }

              .recorder-actions-grid input,
              .recorder-actions-grid textarea {
                padding: 0.5rem 0.75rem;
                border-radius: 8px;
                border: 1px solid #cbd5f5;
                font-family: inherit;
              }

              .recorder-actions-grid textarea {
                resize: vertical;
                min-height: 96px;
              }

              .recorder-options {
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
                font-size: 0.9rem;
              }

              .recorder-options label {
                display: flex;
                align-items: center;
                gap: 0.5rem;
              }

              .recorder-action-buttons {
                display: flex;
                flex-wrap: wrap;
                gap: 0.75rem;
              }

              .recorder-test-actions {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                align-items: center;
                margin-bottom: 0.5rem;
              }

              .recorder-test-actions[hidden] {
                display: none;
              }

              .recorder-test-actions span {
                font-size: 0.85rem;
                color: #475569;
              }

              .recorder-collapse > summary {
                cursor: pointer;
                font-weight: 600;
              }

              .recorder-preview {
                margin: 0;
                background: #0f172a;
                color: #f8fafc;
                padding: 1rem;
                border-radius: 8px;
                font-size: 0.85rem;
                line-height: 1.5;
                max-height: 240px;
                overflow: auto;
                white-space: pre-wrap;
              }

              .recorder-events ol {
                margin: 0;
                padding-left: 1.25rem;
                display: grid;
                gap: 0.5rem;
              }

              .recorder-actions {
                display: flex;
                flex-wrap: wrap;
                gap: 0.75rem;
                align-items: center;
              }

              .recorder-actions input {
                flex: 1;
                min-width: 180px;
                padding: 0.5rem 0.75rem;
                border-radius: 8px;
                border: 1px solid #cbd5f5;
              }

              @media (max-width: 1080px) {
                .recorder-layout {
                  grid-template-columns: 1fr;
                }
              }

              @media (max-width: 960px) {
                .runs-wrapper {
                  grid-template-columns: 1fr;
                }
              }

              @media (max-width: 720px) {
                main {
                  padding: 1.5rem;
                }

                header {
                  padding: 1.5rem;
                }

                .header-controls input {
                  min-width: 200px;
                }
              }
            </style>
            <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
          </head>
          <body>
            <header>
              <div class=\"header-top\">
                <div>
                  <h1>EarMate 监控仪表板</h1>
                  <p>洞察采集任务的运行节奏、指标趋势、录制状态与日志详情。</p>
                </div>
                <nav class=\"view-switch\">
                  <button
                    type=\"button\"
                    data-view-button=\"monitoring\"
                    class=\"active\"
                  >
                    监控总览
                  </button>
                  <button type=\"button\" data-view-button=\"recorder\">录制工作台</button>
                </nav>
              </div>
              <div class=\"header-controls\">
                <label for=\"api-key-input\">API Key（可选）</label>
                <input
                  id=\"api-key-input\"
                  type=\"password\"
                  placeholder=\"填写以启用会话创建及发布操作\"
                />
                <button id=\"api-key-clear\" type=\"button\" class=\"link-button\">清除</button>
                <span id=\"api-key-status\" class=\"status-message\"></span>
              </div>
            </header>
            <main>
              <section class=\"view active\" data-view=\"monitoring\">
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
                      <div id=\"run-detail\" class=\"run-detail\">
                        <pre id=\"run-detail-text\">选择一条执行记录查看日志</pre>
                        <div id=\"run-detail-actions\" class=\"run-detail-actions\"></div>
                      </div>
                    </aside>
                  </div>
                </section>
              </section>

              <section class=\"view\" data-view=\"recorder\">
                <div class=\"recorder-layout\">
                  <aside class=\"recorder-sidebar\">
                    <div class=\"card recorder-actions\">
                      <input id=\"recorder-name\" type=\"text\" placeholder=\"输入会话名称\" />
                      <button id=\"recorder-create\" type=\"button\" class=\"primary-button\">
                        新建会话
                      </button>
                      <button id=\"recorder-refresh\" type=\"button\" class=\"link-button\">
                        刷新列表
                      </button>
                    </div>
                    <div class=\"card\">
                      <div class=\"status-message\" id=\"recorder-status\"></div>
                      <ul id=\"recorder-sessions\" class=\"recorder-sessions\"></ul>
                      <p id=\"recorder-empty\" class=\"empty-state\">暂无录制会话。</p>
                    </div>
                  </aside>
                  <section class=\"recorder-detail\">
                    <div>
                      <h2 style=\"margin-top: 0;\">会话详情</h2>
                      <div id=\"recorder-session-summary\" class=\"recorder-summary\">
                        选择一个会话查看详情
                      </div>
                    </div>
                    <div>
                      <h3 style=\"margin-top: 0;\">事件回放</h3>
                      <div id=\"recorder-events\" class=\"recorder-events\">
                        <p class=\"empty-state\">选择会话后可查看事件序列。</p>
                      </div>
                    </div>
                    <div class=\"recorder-operations\">
                      <h3 style=\"margin-top: 0;\">规则编译与发布</h3>
                      <div class=\"recorder-actions-grid\">
                        <label for=\"recorder-rule-name-input\">规则名称（可选）</label>
                        <input
                          id=\"recorder-rule-name-input\"
                          type=\"text\"
                          placeholder=\"默认使用会话名称\"
                        />
                        <label for=\"recorder-metadata-input\">元数据覆盖（可选，JSON 对象）</label>
                        <textarea
                          id=\"recorder-metadata-input\"
                          placeholder='例如：{"source": "recorder"}'
                        ></textarea>
                        <div class=\"recorder-options\">
                          <label>
                            <input id=\"recorder-enable-toggle\" type=\"checkbox\" checked />
                            发布后启用规则
                          </label>
                          <label>
                            <input id=\"recorder-test-toggle\" type=\"checkbox\" checked />
                            发布时自动试跑
                          </label>
                        </div>
                      </div>
                      <div class=\"recorder-action-buttons\">
                        <button
                          id=\"recorder-compile-btn\"
                          type=\"button\"
                          class=\"secondary-button\"
                        >
                          仅编译
                        </button>
                        <button
                          id=\"recorder-test-btn\"
                          type=\"button\"
                          class=\"secondary-button\"
                        >
                          编译并试跑
                        </button>
                        <button
                          id=\"recorder-publish-btn\"
                          type=\"button\"
                          class=\"primary-button\"
                        >
                          发布规则
                        </button>
                      </div>
                      <div id=\"recorder-operation-status\" class=\"status-message\"></div>
                      <details id=\"recorder-rule-panel\" class=\"recorder-collapse\">
                        <summary>最近一次编译结果</summary>
                        <pre id=\"recorder-rule-preview\" class=\"recorder-preview\">
暂无编译结果。
                        </pre>
                      </details>
                      <details id=\"recorder-test-panel\" class=\"recorder-collapse\">
                        <summary>最近一次试跑结果</summary>
                        <div
                          id=\"recorder-test-actions\"
                          class=\"recorder-test-actions\"
                          hidden
                        ></div>
                        <pre id=\"recorder-test-preview\" class=\"recorder-preview\">
尚未执行试跑。
                        </pre>
                      </details>
                    </div>
                  </section>
                </div>
              </section>
            </main>
            <script>
              window.addEventListener('DOMContentLoaded', () => {
                const elements = {
                  apiKeyInput: document.getElementById('api-key-input'),
                  apiKeyClear: document.getElementById('api-key-clear'),
                  apiKeyStatus: document.getElementById('api-key-status'),
                  viewButtons: Array.from(document.querySelectorAll('[data-view-button]')),
                  views: {
                    monitoring: document.querySelector('[data-view=\"monitoring\"]'),
                    recorder: document.querySelector('[data-view=\"recorder\"]'),
                  },
                  ruleInput: document.getElementById('rule-filter'),
                  refreshButton: document.getElementById('refresh-btn'),
                  lastUpdated: document.getElementById('last-updated'),
                  runsTable: document.getElementById('runs-table'),
                  runsEmpty: document.getElementById('runs-empty'),
                  runDetailText: document.getElementById('run-detail-text'),
                  runDetailActions: document.getElementById('run-detail-actions'),
                  dailyEmpty: document.getElementById('daily-empty'),
                  metricSelect: document.getElementById('metric-select'),
                  metricEmpty: document.getElementById('metric-empty'),
                  recorderName: document.getElementById('recorder-name'),
                  recorderCreate: document.getElementById('recorder-create'),
                  recorderRefresh: document.getElementById('recorder-refresh'),
                  recorderStatus: document.getElementById('recorder-status'),
                  recorderSessions: document.getElementById('recorder-sessions'),
                  recorderEmpty: document.getElementById('recorder-empty'),
                  recorderSummary: document.getElementById('recorder-session-summary'),
                  recorderEvents: document.getElementById('recorder-events'),
                  recorderRuleNameInput: document.getElementById('recorder-rule-name-input'),
                  recorderMetadataInput: document.getElementById('recorder-metadata-input'),
                  recorderEnableToggle: document.getElementById('recorder-enable-toggle'),
                  recorderTestToggle: document.getElementById('recorder-test-toggle'),
                  recorderCompileButton: document.getElementById('recorder-compile-btn'),
                  recorderTestButton: document.getElementById('recorder-test-btn'),
                  recorderPublishButton: document.getElementById('recorder-publish-btn'),
                  recorderOperationStatus: document.getElementById('recorder-operation-status'),
                  recorderRulePanel: document.getElementById('recorder-rule-panel'),
                  recorderRulePreview: document.getElementById('recorder-rule-preview'),
                  recorderTestPanel: document.getElementById('recorder-test-panel'),
                  recorderTestPreview: document.getElementById('recorder-test-preview'),
                  recorderTestActions: document.getElementById('recorder-test-actions'),
                };

                const state = {
                  dailyChart: null,
                  metricChart: null,
                  series: [],
                  apiKey: '',
                  ruleCache: new Map(),
                  sessions: [],
                  selectedSession: null,
                  activeView: 'monitoring',
                  lastCompiledRule: null,
                  lastTestResult: null,
                  recorderBusy: false,
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

                async function requestJSON(url, options = {}) {
                  const config = { method: 'GET', headers: new Headers(), ...options };
                  const requiresBody = config.body && typeof config.body !== 'string';
                  if (requiresBody) {
                    config.body = JSON.stringify(config.body);
                    config.headers.set('Content-Type', 'application/json');
                  }
                  const shouldAttachKey = Boolean(
                    options.requireAuth || (state.apiKey && options.requireAuth !== false),
                  );
                  if (shouldAttachKey && state.apiKey) {
                    config.headers.set('X-API-Key', state.apiKey);
                  }
                  const response = await fetch(url, config);
                  if (!response.ok) {
                    let message = `请求失败: ${response.status}`;
                    try {
                      const payload = await response.json();
                      message = payload.detail || JSON.stringify(payload);
                    } catch (parseError) {
                      // ignore
                    }
                    throw new Error(message);
                  }
                  if (response.status === 204) {
                    return null;
                  }
                  return response.json();
                }

                function updateApiKeyStatus() {
                  if (state.apiKey) {
                    elements.apiKeyStatus.textContent = '已注入 API Key，可执行受保护操作';
                    elements.apiKeyStatus.classList.remove('error');
                  } else {
                    elements.apiKeyStatus.textContent = '未配置 API Key，仅支持查询接口';
                    elements.apiKeyStatus.classList.remove('error');
                  }
                }

                function setApiKey(value) {
                  state.apiKey = value.trim();
                  updateApiKeyStatus();
                  updateRecorderControls();
                }

                function switchView(view) {
                  if (!view || state.activeView === view) {
                    return;
                  }
                  state.activeView = view;
                  Object.entries(elements.views).forEach(([key, node]) => {
                    if (node) {
                      node.classList.toggle('active', key === view);
                    }
                  });
                  elements.viewButtons.forEach((button) => {
                    button.classList.toggle('active', button.dataset.viewButton === view);
                  });
                  if (view === 'recorder') {
                    loadRecorderSessions();
                  }
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
                    row.dataset.ruleId = run.rule_id;
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
                  const dashboard = await requestJSON(`/monitoring/dashboard${query}`, {
                    requireAuth: false,
                  });
                  renderSummary(dashboard.summary || {});
                  renderDaily(dashboard.daily || []);
                  renderMetricOptions(dashboard.series || []);
                }

                async function loadRuns(ruleId) {
                  const query = ruleId ? `?rule_id=${encodeURIComponent(ruleId)}` : '';
                  const runs = await requestJSON(`/monitoring/runs${query}`, {
                    requireAuth: false,
                  });
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

                async function loadRule(ruleId) {
                  if (!ruleId) {
                    return null;
                  }
                  if (state.ruleCache.has(ruleId)) {
                    return state.ruleCache.get(ruleId);
                  }
                  try {
                    const rule = await requestJSON(`/rules/${ruleId}`, { requireAuth: false });
                    state.ruleCache.set(ruleId, rule);
                    return rule;
                  } catch (error) {
                    console.error(error);
                    return null;
                  }
                }

                async function handleRunSelection(row) {
                  const runId = row.dataset.runId;
                  const ruleId = row.dataset.ruleId;
                  elements.runDetailText.textContent = '加载中...';
                  elements.runDetailActions.innerHTML = '';
                  try {
                    const detail = await requestJSON(`/monitoring/runs/${runId}`, {
                      requireAuth: false,
                    });
                    const lines = [];
                    lines.push(`执行 ID: ${detail.id}`);
                    lines.push(`规则 ID: ${detail.rule_id}`);
                    lines.push(`状态: ${detail.status}`);
                    lines.push(`开始时间: ${formatDate(detail.started_at || detail.created_at)}`);
                    lines.push(`结束时间: ${formatDate(detail.finished_at || detail.updated_at)}`);
                    lines.push(`耗时(ms): ${formatDuration(detail.duration_ms)}`);
                    if (detail.execution_id) {
                      lines.push(`执行结果 ID: ${detail.execution_id}`);
                    }
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

                    let recorderSessionId = null;
                    if (ruleId) {
                      const rule = await loadRule(ruleId);
                      const metadata = rule?.rule?.metadata || {};
                      const metadataEntries = Object.entries(metadata);
                      if (metadataEntries.length) {
                        lines.push('\n规则元数据:');
                        metadataEntries.forEach(([key, value]) => {
                          lines.push(`  - ${key}: ${value}`);
                        });
                      }
                      if (typeof metadata.recorder_session === 'string') {
                        recorderSessionId = metadata.recorder_session;
                      }
                    }

                    elements.runDetailText.textContent = lines.join('\n');
                    if (recorderSessionId) {
                      const actionButton = document.createElement('button');
                      actionButton.type = 'button';
                      actionButton.className = 'link-button';
                      actionButton.textContent =
                        `查看关联录制会话 (${recorderSessionId.slice(0, 8)}…)`;
                      actionButton.addEventListener('click', () => {
                        switchView('recorder');
                        focusRecorderSession(recorderSessionId);
                      });
                      elements.runDetailActions.append(actionButton);
                    }
                  } catch (error) {
                    console.error(error);
                    elements.runDetailText.textContent = '日志加载失败，请稍后重试。';
                  }
                }

                async function loadRecorderSessions() {
                  try {
                    elements.recorderStatus.textContent = '加载会话列表中...';
                    elements.recorderStatus.classList.remove('error');
                    const response = await requestJSON('/recorder/sessions', {
                      requireAuth: false,
                    });
                    state.sessions = response.items || [];
                    if (
                      state.selectedSession &&
                      !state.sessions.find((item) => item.id === state.selectedSession)
                    ) {
                      state.selectedSession = null;
                      resetRecorderOutputs();
                    }
                    renderRecorderSessions();
                    if (state.selectedSession) {
                      focusRecorderSession(state.selectedSession);
                    }
                    if (!state.sessions.length) {
                      elements.recorderStatus.textContent = '暂无会话，使用 API Key 可创建新会话。';
                    } else {
                      elements.recorderStatus.textContent = `共 ${state.sessions.length} 个会话`;
                    }
                    updateRecorderControls();
                  } catch (error) {
                    console.error(error);
                    elements.recorderStatus.textContent = `会话列表加载失败：${error.message}`;
                    elements.recorderStatus.classList.add('error');
                  }
                }

                function renderRecorderSessions() {
                  elements.recorderSessions.innerHTML = '';
                  if (!state.sessions.length) {
                    elements.recorderEmpty.hidden = false;
                    return;
                  }
                  elements.recorderEmpty.hidden = true;
                  const fragment = document.createDocumentFragment();
                  state.sessions.forEach((session) => {
                    const item = document.createElement('li');
                    item.className = 'recorder-session';
                    item.dataset.sessionId = session.id;
                    if (state.selectedSession === session.id) {
                      item.classList.add('active');
                    }
                    item.innerHTML = `
                      <h3>${session.name || '未命名会话'}</h3>
                      <div>${session.metadata?.entry || session.entry || '未配置入口 URL'}</div>
                      <small>
                        事件数：${session.event_count} · 创建时间：${formatDate(session.created_at)}
                      </small>
                    `;
                    fragment.append(item);
                  });
                  elements.recorderSessions.append(fragment);
                }

                function selectRecorderSession(sessionId) {
                  const previous = state.selectedSession;
                  state.selectedSession = sessionId;
                  Array.from(elements.recorderSessions.children).forEach((node) => {
                    node.classList.toggle('active', node.dataset.sessionId === sessionId);
                  });
                  if (previous !== sessionId) {
                    resetRecorderOutputs();
                  }
                  updateRecorderControls();
                }

                async function focusRecorderSession(sessionId) {
                  if (!sessionId) {
                    return;
                  }
                  if (!state.sessions.find((item) => item.id === sessionId)) {
                    await loadRecorderSessions();
                  }
                  selectRecorderSession(sessionId);
                  await loadRecorderDetail(sessionId);
                }

                async function loadRecorderDetail(sessionId) {
                  elements.recorderSummary.textContent = '加载会话详情...';
                  elements.recorderEvents.innerHTML =
                    '<p class="empty-state">加载事件序列中...</p>';
                  try {
                    const [session, playback] = await Promise.all([
                      requestJSON(`/recorder/sessions/${sessionId}`, {
                        requireAuth: false,
                      }),
                      requestJSON(`/recorder/sessions/${sessionId}/playback`, {
                        requireAuth: false,
                      }),
                    ]);
                    renderRecorderDetail(session, playback.events || []);
                  } catch (error) {
                    console.error(error);
                    elements.recorderSummary.textContent = '会话详情加载失败，请稍后重试。';
                    elements.recorderEvents.innerHTML =
                      `<p class="empty-state">${error.message}</p>`;
                  }
                }

                function renderRecorderDetail(session, events) {
                  const lines = [];
                  lines.push(`会话 ID: ${session.id}`);
                  lines.push(`名称: ${session.name || '未命名会话'}`);
                  lines.push(`入口 URL: ${session.entry || '未设置'}`);
                  lines.push(`事件总数: ${session.event_count}`);
                  lines.push(`创建时间: ${formatDate(session.created_at)}`);
                  lines.push(`最近更新时间: ${formatDate(session.updated_at)}`);
                  if (session.metadata && Object.keys(session.metadata).length) {
                    lines.push('\n元数据:');
                    Object.entries(session.metadata).forEach(([key, value]) => {
                      lines.push(`  - ${key}: ${value}`);
                    });
                  }
                  elements.recorderSummary.textContent = lines.join('\n');

                  if (!events.length) {
                    elements.recorderEvents.innerHTML = '<p class="empty-state">暂无录制事件。</p>';
                    return;
                  }
                  const list = document.createElement('ol');
                  events.forEach((event) => {
                    const item = document.createElement('li');
                    item.innerHTML = `
                      <strong>${event.type}</strong>
                      <div><small>${formatDate(event.timestamp)}</small></div>
                      <pre>${JSON.stringify(event.payload, null, 2)}</pre>
                    `;
                    list.append(item);
                  });
                  elements.recorderEvents.innerHTML = '';
                  elements.recorderEvents.append(list);
                }

                function setRecorderOperationStatus(message, isError = false) {
                  if (!elements.recorderOperationStatus) {
                    return;
                  }
                  elements.recorderOperationStatus.textContent = message || '';
                  elements.recorderOperationStatus.classList.toggle('error', Boolean(isError));
                }

                function renderRulePreview(rule) {
                  if (!elements.recorderRulePreview || !elements.recorderRulePanel) {
                    return;
                  }
                  if (!rule) {
                    elements.recorderRulePreview.textContent = '暂无编译结果。';
                    elements.recorderRulePanel.open = false;
                    return;
                  }
                  elements.recorderRulePreview.textContent = JSON.stringify(rule, null, 2);
                  elements.recorderRulePanel.open = true;
                }

                function renderTestResult(result) {
                  if (!elements.recorderTestPreview || !elements.recorderTestPanel) {
                    return;
                  }
                  if (elements.recorderTestActions) {
                    elements.recorderTestActions.innerHTML = '';
                    elements.recorderTestActions.hidden = true;
                  }
                  if (!result) {
                    elements.recorderTestPreview.textContent = '尚未执行试跑。';
                    elements.recorderTestPanel.open = false;
                    return;
                  }
                  const records = Array.isArray(result.records) ? result.records : [];
                  const detailRecords = Array.isArray(result.detail_records)
                    ? result.detail_records
                    : [];
                  const lines = [];
                  lines.push(`列表记录：${records.length}`);
                  lines.push(`详情记录：${detailRecords.length}`);
                  const metadata = result.metadata && typeof result.metadata === 'object'
                    ? result.metadata
                    : {};
                  if (Object.keys(metadata).length) {
                    lines.push('\n元数据:');
                    Object.entries(metadata).forEach(([key, value]) => {
                      lines.push(`  - ${key}: ${value}`);
                    });
                  }
                  if (records.length) {
                    lines.push('\n示例记录:');
                    lines.push(JSON.stringify(records[0], null, 2));
                  }
                  elements.recorderTestPreview.textContent = lines.join('\n');
                  const monitoring =
                    result.monitoring && typeof result.monitoring === 'object'
                      ? result.monitoring
                      : null;
                  if (monitoring && elements.recorderTestActions) {
                    elements.recorderTestActions.hidden = false;
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'link-button';
                    button.textContent = '查看执行监控';
                    button.addEventListener('click', async () => {
                      switchView('monitoring');
                      try {
                        if (
                          monitoring.rule_id &&
                          typeof monitoring.rule_id === 'string' &&
                          elements.ruleInput
                        ) {
                          elements.ruleInput.value = monitoring.rule_id;
                        }
                        await refresh();
                        if (
                          monitoring.run_id &&
                          typeof monitoring.run_id === 'string' &&
                          elements.runsTable
                        ) {
                          const rows = Array.from(elements.runsTable.querySelectorAll('tr'));
                          const target = rows.find(
                            (item) => item.dataset.runId === monitoring.run_id,
                          );
                          if (target) {
                            target.click();
                            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                          }
                        }
                      } catch (error) {
                        console.error(error);
                      }
                    });
                    elements.recorderTestActions.append(button);
                    if (typeof monitoring.run_id === 'string' && monitoring.run_id) {
                      const runLabel = document.createElement('span');
                      runLabel.textContent = `运行 ID：${monitoring.run_id}`;
                      elements.recorderTestActions.append(runLabel);
                    }
                    if (typeof monitoring.rule_id === 'string' && monitoring.rule_id) {
                      const ruleLabel = document.createElement('span');
                      ruleLabel.textContent = `规则 ID：${monitoring.rule_id}`;
                      elements.recorderTestActions.append(ruleLabel);
                    }
                  }
                  elements.recorderTestPanel.open = true;
                }

                function resetRecorderOutputs() {
                  state.lastCompiledRule = null;
                  state.lastTestResult = null;
                  renderRulePreview(null);
                  renderTestResult(null);
                  if (state.selectedSession) {
                    setRecorderOperationStatus('已切换会话，请先执行编译。');
                  } else {
                    setRecorderOperationStatus('请选择左侧的录制会话开始操作。');
                  }
                }

                function updateRecorderControls() {
                  const hasSession = Boolean(state.selectedSession);
                  const hasApiKey = Boolean(state.apiKey);
                  const disabled = state.recorderBusy || !hasSession || !hasApiKey;
                  [
                    elements.recorderCompileButton,
                    elements.recorderTestButton,
                    elements.recorderPublishButton,
                  ].forEach((button) => {
                    if (button) {
                      button.disabled = disabled;
                    }
                  });
                }

                function ensureRecorderReady() {
                  if (!state.selectedSession) {
                    setRecorderOperationStatus('请选择左侧的录制会话。', true);
                    return false;
                  }
                  if (!state.apiKey) {
                    setRecorderOperationStatus('请先在顶部输入有效的 API Key。', true);
                    return false;
                  }
                  return true;
                }

                function parseMetadataInput() {
                  if (!elements.recorderMetadataInput) {
                    return null;
                  }
                  const raw = elements.recorderMetadataInput.value.trim();
                  if (!raw) {
                    return null;
                  }
                  try {
                    const parsed = JSON.parse(raw);
                    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
                      throw new Error('请输入对象格式的 JSON');
                    }
                    const invalidEntry = Object.entries(parsed).find(
                      ([, value]) => typeof value !== 'string',
                    );
                    if (invalidEntry) {
                      throw new Error('元数据的值必须为字符串');
                    }
                    return parsed;
                  } catch (error) {
                    throw new Error(`元数据解析失败：${error.message}`);
                  }
                }

                async function compileSessionOnce() {
                  const sessionId = state.selectedSession;
                  if (!sessionId) {
                    throw new Error('请选择左侧的录制会话。');
                  }
                  const name = elements.recorderRuleNameInput
                    ? elements.recorderRuleNameInput.value.trim()
                    : '';
                  const payload = name ? { name } : {};
                  const response = await requestJSON(`/recorder/sessions/${sessionId}/compile`, {
                    method: 'POST',
                    body: payload,
                    requireAuth: true,
                  });
                  state.lastCompiledRule = response.rule;
                  renderRulePreview(response.rule);
                  return response.rule;
                }

                async function handleCompile() {
                  if (!ensureRecorderReady()) {
                    return;
                  }
                  state.recorderBusy = true;
                  updateRecorderControls();
                  setRecorderOperationStatus('正在编译录制会话...', false);
                  try {
                    await compileSessionOnce();
                    state.lastTestResult = null;
                    renderTestResult(null);
                    setRecorderOperationStatus('编译成功，可继续试跑或发布。');
                  } catch (error) {
                    console.error(error);
                    setRecorderOperationStatus(`编译失败：${error.message}`, true);
                  } finally {
                    state.recorderBusy = false;
                    updateRecorderControls();
                  }
                }

                async function handleTestRun() {
                  if (!ensureRecorderReady()) {
                    return;
                  }
                  state.recorderBusy = true;
                  updateRecorderControls();
                  try {
                    setRecorderOperationStatus('正在编译录制会话...', false);
                    const rule = await compileSessionOnce();
                    setRecorderOperationStatus('编译成功，正在执行试跑...', false);
                    const result = await requestJSON('/rules/test-run', {
                      method: 'POST',
                      body: rule,
                      requireAuth: true,
                    });
                    state.lastTestResult = result;
                    renderTestResult(result);
                    setRecorderOperationStatus('试跑成功，结果已更新。');
                  } catch (error) {
                    console.error(error);
                    setRecorderOperationStatus(`试跑失败：${error.message}`, true);
                  } finally {
                    state.recorderBusy = false;
                    updateRecorderControls();
                  }
                }

                async function handlePublish() {
                  if (!ensureRecorderReady()) {
                    return;
                  }
                  let metadataOverride = null;
                  try {
                    metadataOverride = parseMetadataInput();
                  } catch (error) {
                    console.error(error);
                    setRecorderOperationStatus(error.message, true);
                    return;
                  }
                  state.recorderBusy = true;
                  updateRecorderControls();
                  try {
                    setRecorderOperationStatus('正在发布规则...', false);
                    const sessionId = state.selectedSession;
                    const name = elements.recorderRuleNameInput
                      ? elements.recorderRuleNameInput.value.trim()
                      : '';
                    const payload = {
                      enable: Boolean(elements.recorderEnableToggle?.checked),
                      test_run: Boolean(elements.recorderTestToggle?.checked),
                    };
                    if (name) {
                      payload.name = name;
                    }
                    if (metadataOverride) {
                      payload.metadata = metadataOverride;
                    }
                    const response = await requestJSON(
                      `/recorder/sessions/${sessionId}/publish`,
                      {
                        method: 'POST',
                        body: payload,
                        requireAuth: true,
                      },
                    );
                    const ruleRecord = response.rule || null;
                    if (ruleRecord) {
                      state.ruleCache.set(ruleRecord.id, ruleRecord);
                      if (ruleRecord.rule) {
                        state.lastCompiledRule = ruleRecord.rule;
                        renderRulePreview(ruleRecord.rule);
                      }
                    }
                    if (response.test_run) {
                      state.lastTestResult = response.test_run;
                      renderTestResult(response.test_run);
                    } else {
                      state.lastTestResult = null;
                      renderTestResult(null);
                    }
                    const ruleId = ruleRecord?.id ? `规则已发布：${ruleRecord.id}` : '规则已发布。';
                    setRecorderOperationStatus(ruleId);
                  } catch (error) {
                    console.error(error);
                    setRecorderOperationStatus(`发布失败：${error.message}`, true);
                  } finally {
                    state.recorderBusy = false;
                    updateRecorderControls();
                  }
                }

                async function createRecorderSession() {
                  const name = elements.recorderName.value.trim();
                  try {
                    const payload = name ? { name } : {};
                    const response = await requestJSON('/recorder/sessions', {
                      method: 'POST',
                      body: payload,
                      requireAuth: true,
                    });
                    elements.recorderName.value = '';
                    state.selectedSession = response.id;
                    await loadRecorderSessions();
                    elements.recorderStatus.textContent = `会话已创建：${response.id}`;
                    elements.recorderStatus.classList.remove('error');
                    focusRecorderSession(response.id);
                  } catch (error) {
                    console.error(error);
                    elements.recorderStatus.textContent = `创建失败：${error.message}`;
                    elements.recorderStatus.classList.add('error');
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

                elements.runsTable.addEventListener('click', (event) => {
                  const row = event.target.closest('tr[data-run-id]');
                  if (!row) {
                    return;
                  }
                  handleRunSelection(row);
                });

                elements.recorderSessions.addEventListener('click', (event) => {
                  const item = event.target.closest('li[data-session-id]');
                  if (!item) {
                    return;
                  }
                  const { sessionId } = item.dataset;
                  selectRecorderSession(sessionId);
                  loadRecorderDetail(sessionId);
                });

                elements.recorderRefresh.addEventListener('click', () => {
                  loadRecorderSessions();
                });

                elements.recorderCreate.addEventListener('click', () => {
                  if (!state.apiKey) {
                    elements.recorderStatus.textContent = '请先在顶部输入有效的 API Key';
                    elements.recorderStatus.classList.add('error');
                    return;
                  }
                  createRecorderSession();
                });

                elements.recorderCompileButton.addEventListener('click', handleCompile);
                elements.recorderTestButton.addEventListener('click', handleTestRun);
                elements.recorderPublishButton.addEventListener('click', handlePublish);

                elements.apiKeyInput.addEventListener('input', (event) => {
                  setApiKey(event.target.value);
                });

                elements.apiKeyClear.addEventListener('click', () => {
                  elements.apiKeyInput.value = '';
                  setApiKey('');
                });

                elements.viewButtons.forEach((button) => {
                  button.addEventListener('click', () => {
                    switchView(button.dataset.viewButton);
                  });
                });

                resetRecorderOutputs();
                updateRecorderControls();
                updateApiKeyStatus();
                refresh();
              });
            </script>
          </body>
        </html>
        """
    ).strip()
