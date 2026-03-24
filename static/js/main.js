/**
 * 麥當勞品牌輿情監控系統 - 前端互動邏輯
 */

// =============================================================================
// 全域狀態
// =============================================================================
let trendChart = null;
let sourcePieChart = null;
let currentPage = 1;

// Chart.js 全域設定
Chart.defaults.color = '#9898AA';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
Chart.defaults.font.family = "'Inter', 'Noto Sans TC', sans-serif";

// =============================================================================
// 初始化
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    loadStats();
    loadSummaries();
    loadDailyStats(7);
    loadArticles();
    loadLogs();

    // 綁定統計卡片點擊
    document.getElementById('stat-total').onclick = () => openModal('total');
    document.getElementById('stat-positive').onclick = () => openModal('positive');
    document.getElementById('stat-negative').onclick = () => openModal('negative');
    document.getElementById('stat-neutral').onclick = () => openModal('neutral');

    // 綁定 AI 洞察卡片點擊
    document.querySelector('.insight-positive').onclick = () => openModal('insight_pos');
    document.querySelector('.insight-negative').onclick = () => openModal('insight_neg');
    document.querySelector('.insight-neutral').onclick = () => openModal('insight_neu');

    // 每 60 秒自動重新整理統計
    setInterval(() => {
        loadStats();
        loadSummaries();
    }, 60000);
});

// =============================================================================
// 詳細報表彈窗
// =============================================================================
async function openModal(type) {
    const modal = document.getElementById('detail-modal');
    const titleEl = document.getElementById('modal-title');
    const bodyEl = document.getElementById('modal-body');
    
    modal.classList.add('active');
    document.body.style.overflow = 'hidden'; // 禁止背景捲動
    bodyEl.innerHTML = '<div class="loading-placeholder"><div class="spinner"></div><p>載入中...</p></div>';

    let title = "";
    let sentiment = "all";
    
    // 設定標題與篩選類型
    switch(type) {
        case 'total': title = "📄 全平台文章明細"; sentiment = "all"; break;
        case 'positive': title = "🟢 正面評價明細"; sentiment = "positive"; break;
        case 'negative': title = "🔴 負面輿情明細"; sentiment = "negative"; break;
        case 'neutral': title = "⚪ 中立評價明細"; sentiment = "neutral"; break;
        case 'insight_pos': title = "💡 正面亮點詳細分析"; break;
        case 'insight_neg': title = "⚠️ 負面痛點深度報告"; break;
        case 'insight_neu': title = "🧭 品牌綜合觀察週報"; break;
    }
    
    titleEl.textContent = title;

    try {
        if (type.startsWith('insight')) {
            // AI 摘要詳細版 (包含代表性文章)
            const sentimentKey = type.split('_')[1]; // pos, neg, neu
            const mapping = { 'pos': 'positive', 'neg': 'negative', 'neu': 'neutral' };
            const fullSentiment = mapping[sentimentKey];
            
            const [summaryResp, articleResp] = await Promise.all([
                fetch('/api/summaries'),
                fetch(`/api/articles?sentiment=${fullSentiment}&per_page=10`)
            ]);
            const summaryData = await summaryResp.json();
            const articleData = await articleResp.json();
            
            bodyEl.innerHTML = `
                <div class="modal-report-section">
                    <h3 style="color: var(--mcd-red); margin-bottom: 12px; font-size: 18px;">【AI 專家深度診斷】</h3>
                    <div style="font-size: 15px; line-height: 1.8; color: var(--text-primary); margin-bottom: 32px; padding: 20px; background: var(--bg-primary); border-radius: 12px; border-left: 5px solid var(--mcd-yellow); box-shadow: var(--shadow-soft);">
                        ${summaryData[fullSentiment].summary}
                    </div>
                    
                    <h3 style="margin-bottom: 16px; font-size: 18px; display: flex; align-items: center; gap: 8px;">
                        <span>📚 最新相關文章參考</span>
                        <small style="font-size: 12px; font-weight: normal; color: var(--text-muted);">(顯示最近 ${articleData.articles.length} 篇)</small>
                    </h3>
                    <div class="modal-article-list">
                        ${articleData.articles.map(a => renderArticleCard(a)).join('')}
                    </div>
                </div>
            `;
        } else {
            // 文章清單版
            const resp = await fetch(`/api/articles?sentiment=${sentiment}&per_page=100`);
            const data = await resp.json();
            
            bodyEl.innerHTML = `
                <div class="modal-list-stats" style="margin-bottom: 24px; padding: 12px 20px; background: var(--bg-secondary); border-radius: 8px; color: var(--text-secondary); font-weight: 500;">
                    📊 目前系統共搜集到 ${data.total} 篇相關文章 (此處預覽最後 100 篇)
                </div>
                <div class="articles-list">
                    ${data.articles.map(a => renderArticleCard(a)).join('')}
                </div>
            `;
        }
    } catch (err) {
        bodyEl.innerHTML = `
            <div class="loading-placeholder">
                <p style="color: var(--negative);">⚠️ 載入詳細報表失敗: ${err.message}</p>
            </div>
        `;
    }
}

function closeModal() {
    document.getElementById('detail-modal').classList.remove('active');
    document.body.style.overflow = ''; // 恢復捲動
}

// =============================================================================
// AI 摘要
// =============================================================================
async function loadSummaries() {
    try {
        const resp = await fetch('/api/summaries');
        const data = await resp.json();

        document.getElementById('summary-positive').textContent = data.positive.summary;
        document.getElementById('summary-negative').textContent = data.negative.summary;
        document.getElementById('summary-neutral').textContent = data.neutral.summary;
    } catch (err) {
        console.error('載入 AI 摘要失敗:', err);
    }
}

// =============================================================================
// 統計資料
// =============================================================================
async function loadStats() {
    try {
        const resp = await fetch('/api/stats?days=7');
        const stats = await resp.json();

        animateValue('stat-total-value', stats.total || 0);
        animateValue('stat-positive-value', stats.positive || 0);
        animateValue('stat-negative-value', stats.negative || 0);
        animateValue('stat-neutral-value', stats.neutral || 0);

        // 更新環形進度
        const total = stats.total || 1;
        updateRing('ring-positive', (stats.positive / total) * 100);
        updateRing('ring-negative', (stats.negative / total) * 100);
        updateRing('ring-neutral', (stats.neutral / total) * 100);

        // 更新來源分佈圖
        loadSourceStats();
    } catch (err) {
        console.error('載入統計資料失敗:', err);
    }
}

async function loadSourceStats() {
    try {
        const resp = await fetch('/api/source-stats?days=7');
        const stats = await resp.json();

        if (sourcePieChart) {
            sourcePieChart.data.labels = stats.map(s => s.source);
            sourcePieChart.data.datasets[0].data = stats.map(s => s.count);
            sourcePieChart.update('none');
        }
    } catch (err) {
        console.error('載入來源統計失敗:', err);
    }
}

function animateValue(elementId, target) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const current = parseInt(el.textContent) || 0;
    if (current === target) {
        el.textContent = target;
        return;
    }

    const duration = 600;
    const start = performance.now();

    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = Math.round(current + (target - current) * eased);
        el.textContent = value;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function updateRing(elementId, percentage) {
    const el = document.getElementById(elementId);
    if (el) {
        el.setAttribute('stroke-dasharray', `${percentage}, 100`);
    }
}

// =============================================================================
// 圖表
// =============================================================================
function initCharts() {
    // 趨勢折線圖
    const trendCtx = document.getElementById('trend-chart');
    if (trendCtx) {
        trendChart = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '正面',
                        data: [],
                        borderColor: '#22C55E',
                        backgroundColor: 'rgba(34, 197, 94, 0.08)',
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#22C55E',
                        pointBorderColor: '#0A0A0F',
                        pointBorderWidth: 2,
                    },
                    {
                        label: '負面',
                        data: [],
                        borderColor: '#EF4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.08)',
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#EF4444',
                        pointBorderColor: '#0A0A0F',
                        pointBorderWidth: 2,
                    },
                    {
                        label: '中立',
                        data: [],
                        borderColor: '#A78BFA',
                        backgroundColor: 'rgba(167, 139, 250, 0.05)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 2,
                        pointHoverRadius: 5,
                        pointBackgroundColor: '#A78BFA',
                        pointBorderColor: '#0A0A0F',
                        pointBorderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 20,
                            font: { size: 12, weight: '500' },
                        },
                    },
                    tooltip: {
                        backgroundColor: 'rgba(26, 26, 37, 0.95)',
                        titleFont: { size: 13, weight: '600' },
                        bodyFont: { size: 12 },
                        padding: 12,
                        cornerRadius: 8,
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 }, maxRotation: 0 },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.04)' },
                        ticks: {
                            font: { size: 11 },
                            stepSize: 1,
                            precision: 0,
                        },
                    },
                },
            },
        });
    }

    // 來源分佈圓餅圖
    const sourcePieCtx = document.getElementById('source-pie-chart');
    if (sourcePieCtx) {
        sourcePieChart = new Chart(sourcePieCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        'rgba(218, 41, 28, 0.8)',   // McDonald Red
                        'rgba(255, 199, 44, 0.8)',  // McDonald Yellow
                        'rgba(34, 197, 94, 0.8)',   // Green
                        'rgba(59, 130, 246, 0.8)',  // Blue
                        'rgba(167, 139, 250, 0.8)', // Purple
                        'rgba(245, 158, 11, 0.8)',  // Orange
                        'rgba(236, 72, 153, 0.8)',  // Pink
                        'rgba(107, 114, 128, 0.8)', // Gray
                    ],
                    borderColor: '#1A1A25',
                    borderWidth: 3,
                    hoverOffset: 8,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 16,
                            font: { size: 10, weight: '500' },
                        },
                    },
                    tooltip: {
                        backgroundColor: 'rgba(26, 26, 37, 0.95)',
                        padding: 12,
                        cornerRadius: 8,
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0
                                    ? ((context.parsed / total) * 100).toFixed(1)
                                    : 0;
                                return ` ${context.label}: ${context.parsed} 篇 (${pct}%)`;
                            },
                        },
                    },
                },
            },
        });
    }
}

async function loadDailyStats(days) {
    try {
        const resp = await fetch(`/api/daily-stats?days=${days}`);
        const data = await resp.json();

        if (!trendChart) return;

        trendChart.data.labels = data.map(d => {
            const parts = d.date.split('-');
            return `${parts[1]}/${parts[2]}`;
        });
        trendChart.data.datasets[0].data = data.map(d => d.positive || 0);
        trendChart.data.datasets[1].data = data.map(d => d.negative || 0);
        trendChart.data.datasets[2].data = data.map(d => d.neutral || 0);
        trendChart.update();
    } catch (err) {
        console.error('載入每日統計失敗:', err);
    }
}

function updateChartDays(days, btn) {
    // 更新 active chip
    document.querySelectorAll('.chart-controls .chip').forEach(c => c.classList.remove('active'));
    if (btn) btn.classList.add('active');
    loadDailyStats(days);
}

// =============================================================================
// 文章列表
// =============================================================================
async function loadArticles(page = 1) {
    currentPage = page;
    const sentiment = document.getElementById('filter-sentiment').value;
    const source = document.getElementById('filter-source').value;
    const days = document.getElementById('filter-days').value;

    const listEl = document.getElementById('articles-list');
    listEl.innerHTML = `
        <div class="loading-placeholder">
            <div class="spinner"></div>
            <p>載入中...</p>
        </div>
    `;

    try {
        const params = new URLSearchParams({
            sentiment, source, days, page, per_page: 20,
        });
        const resp = await fetch(`/api/articles?${params}`);
        const data = await resp.json();

        if (data.articles.length === 0) {
            listEl.innerHTML = `
                <div class="loading-placeholder">
                    <p style="font-size: 36px; margin-bottom: 8px;">📭</p>
                    <p>目前沒有符合條件的文章</p>
                    <p style="font-size: 12px; color: var(--text-muted);">
                        新的資料將在下次排程任務（07:00）自動搜集
                    </p>
                </div>
            `;
        } else {
            listEl.innerHTML = data.articles.map(article => renderArticleCard(article)).join('');
        }

        renderPagination(data.page, data.pages);
    } catch (err) {
        console.error('載入文章失敗:', err);
        listEl.innerHTML = `
            <div class="loading-placeholder">
                <p>⚠️ 載入失敗，請稍後再試</p>
            </div>
        `;
    }
}

function renderArticleCard(article) {
    const sentimentEmoji = {
        positive: '😊',
        negative: '😟',
        neutral: '😐',
    };
    const sentimentLabel = {
        positive: '正面',
        negative: '負面',
        neutral: '中立',
    };

    const emoji = sentimentEmoji[article.sentiment] || '😐';
    const label = sentimentLabel[article.sentiment] || '中立';
    const cls = article.sentiment || 'neutral';

    const title = escapeHtml(article.title || '無標題');
    const summary = escapeHtml(article.summary || article.content || '');
    const source = escapeHtml(article.source || '');
    const reason = escapeHtml(article.sentiment_reason || '');
    const publishedAt = formatDate(article.published_at);
    const url = article.url || '#';

    return `
        <div class="article-card">
            <div class="article-sentiment ${cls}">${emoji}</div>
            <div class="article-content">
                <div class="article-title">
                    <a href="${url}" target="_blank" rel="noopener">${title}</a>
                </div>
                ${summary ? `<div class="article-summary">${summary}</div>` : ''}
                <div class="article-meta">
                    <span class="article-tag ${cls}">${label}</span>
                    <span>📰 ${source}</span>
                    <span>🕐 ${publishedAt}</span>
                    ${reason ? `<span class="article-reason">💬 ${reason}</span>` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderPagination(current, total) {
    const el = document.getElementById('pagination');
    if (!el || total <= 1) {
        if (el) el.innerHTML = '';
        return;
    }

    let html = '';
    html += `<button ${current <= 1 ? 'disabled' : ''} onclick="loadArticles(${current - 1})">‹ 上一頁</button>`;

    const maxVisible = 5;
    let start = Math.max(1, current - Math.floor(maxVisible / 2));
    let end = Math.min(total, start + maxVisible - 1);
    start = Math.max(1, end - maxVisible + 1);

    if (start > 1) {
        html += `<button onclick="loadArticles(1)">1</button>`;
        if (start > 2) html += `<button disabled>…</button>`;
    }

    for (let i = start; i <= end; i++) {
        html += `<button class="${i === current ? 'active' : ''}" onclick="loadArticles(${i})">${i}</button>`;
    }

    if (end < total) {
        if (end < total - 1) html += `<button disabled>…</button>`;
        html += `<button onclick="loadArticles(${total})">${total}</button>`;
    }

    html += `<button ${current >= total ? 'disabled' : ''} onclick="loadArticles(${current + 1})">下一頁 ›</button>`;

    el.innerHTML = html;
}

// =============================================================================
// 執行記錄
// =============================================================================
async function loadLogs() {
    try {
        const resp = await fetch('/api/logs?limit=50');
        const logs = await resp.json();

        const tbody = document.getElementById('logs-body');
        if (!tbody) return;

        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="empty-state">尚無執行記錄</td></tr>';
            return;
        }

        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${formatDate(log.run_at)}</td>
                <td>${log.total_collected}</td>
                <td>${log.total_analyzed}</td>
                <td style="color: var(--positive)">${log.positive_count}</td>
                <td style="color: var(--negative)">${log.negative_count}</td>
                <td style="color: var(--neutral)">${log.neutral_count}</td>
                <td>${log.notification_sent}</td>
                <td>
                    <span class="status-badge ${log.status}">
                        ${log.status === 'success' ? '✓ 成功' : '✗ 失敗'}
                    </span>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('載入執行記錄失敗:', err);
    }
}

// =============================================================================
// 工具函式
// =============================================================================
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 4000);
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;

        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        return `${month}/${day} ${hours}:${minutes}`;
    } catch {
        return dateStr;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}
