// app.js — 强化实时仪表盘脚本
let currentStock = '600519';

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('stockSelect')?.addEventListener('change', e => {
        currentStock = e.target.value;
        refreshChart();
    });
    refreshAll();
    setInterval(refreshAll, 8000);
});

function refreshAll() {
    loadStatus();
    loadPositions();
    loadWeights();
    loadPerformance();
    loadHistory();
    loadLogs();
    refreshChart();
}

// —— 账户状态 ——
async function loadStatus() {
    const res = await fetch('/api/status');
    const data = await res.json();
    document.getElementById('totalAsset').textContent = '¥' + (data.total_asset?.toLocaleString() || '--');
    document.getElementById('cash').textContent = '¥' + (data.cash?.toLocaleString() || '--');
    document.getElementById('drawdown').textContent = (data.drawdown * 100).toFixed(2) + '%';
    document.getElementById('lossStreak').textContent = data.loss_streak || 0;
}

// —— 持仓表 ——
async function loadPositions() {
    const res = await fetch('/api/positions');
    const data = await res.json();
    const container = document.getElementById('positionsTable');
    if (!data || Object.keys(data).length === 0) {
        container.innerHTML = '无持仓'; return;
    }
    let html = '<table style="width:100%; border-collapse:collapse;">';
    html += '<tr style="color:#94a3b8;"><th>股票</th><th>数量</th></tr>';
    for (let [stock, amt] of Object.entries(data)) {
        html += `<tr><td>${stock}</td><td>${amt}</td></tr>`;
    }
    html += '</table>';
    container.innerHTML = html;
}

// —— 模型权重柱状图 ——
async function loadWeights() {
    const res = await fetch('/api/model_weights');
    const weights = await res.json();
    const keys = Object.keys(weights);
    const values = Object.values(weights);
    const trace = { x: keys, y: values, type: 'bar', marker: {color: '#38bdf8'} };
    const layout = {
        paper_bgcolor: '#111827', plot_bgcolor: '#111827',
        font: { color: '#e2e8f0' }, margin: { t: 10, b: 40, l: 40, r: 10 },
        yaxis: { title: '权重' }
    };
    Plotly.newPlot('weightChart', [trace], layout, {responsive: true});
}

// —— 净值曲线 ——
async function loadPerformance() {
    const res = await fetch('/api/performance');
    const data = await res.json();
    const snapshots = data.snapshots || [];
    if (!snapshots.length) return;
    const trace = {
        x: snapshots.map(s => s.date),
        y: snapshots.map(s => s.total_asset),
        type: 'scatter', mode: 'lines', fill: 'tozeroy',
        line: { color: '#4ade80' }
    };
    const layout = {
        paper_bgcolor: '#111827', plot_bgcolor: '#111827',
        font: { color: '#e2e8f0' }, margin: { t: 10, b: 40, l: 50, r: 10 },
        xaxis: { title: '日期' }, yaxis: { title: '资产' }
    };
    Plotly.newPlot('equityChart', [trace], layout, {responsive: true});
}

// —— 交易历史 ——
async function loadHistory() {
    const res = await fetch('/api/history');
    const trades = await res.json();
    const div = document.getElementById('tradeHistory');
    if (!trades.length) { div.innerHTML = '暂无交易'; return; }
    div.innerHTML = trades.slice(-10).map(t =>
        `<div style="margin:2px 0;">
            ${t.time} | ${t.action} ${t.stock} @ ${t.price} x${t.amount} | 盈亏 ${t.profit?.toFixed(2) || '--'}
        </div>`
    ).join('');
}

// —— 日志 ——
async function loadLogs() {
    const res = await fetch('/api/logs');
    const lines = await res.json();
    const container = document.getElementById('logs');
    container.innerHTML = lines.map(l => {
        let cls = '';
        if (l.includes('🛑') || l.includes('RISK')) cls = 'warn';
        if (l.includes('❌')) cls = 'err';
        return `<div class="log-line ${cls}">${escapeHtml(l)}</div>`;
    }).join('');
    container.scrollTop = container.scrollHeight;
}

// —— K线图 + 信号 ——
async function refreshChart() {
    const res = await fetch(`/api/kline/${currentStock}`);
    const data = await res.json();
    const candles = data.candles;
    const signals = data.signals;
    const traceCandle = {
        x: candles.map(c => c.time), open: candles.map(c => c.open),
        high: candles.map(c => c.high), low: candles.map(c => c.low),
        close: candles.map(c => c.close),
        type: 'candlestick', name: currentStock,
        increasing: { line: { color: '#4ade80' } }, decreasing: { line: { color: '#f87171' } }
    };
    const buySignals = signals.filter(s => s.type === 'buy').map(s => ({...s, price: candles.find(c => c.time === s.time)?.low}));
    const sellSignals = signals.filter(s => s.type === 'sell').map(s => ({...s, price: candles.find(c => c.time === s.time)?.high}));
    const traceBuy = {
        x: buySignals.map(s => s.time), y: buySignals.map(s => s.price),
        mode: 'markers', type: 'scatter', name: 'BUY',
        marker: { color: '#4ade80', size: 10, symbol: 'triangle-up' }
    };
    const traceSell = {
        x: sellSignals.map(s => s.time), y: sellSignals.map(s => s.price),
        mode: 'markers', type: 'scatter', name: 'SELL',
        marker: { color: '#f87171', size: 10, symbol: 'triangle-down' }
    };
    Plotly.newPlot('chart', [traceCandle, traceBuy, traceSell], {
        paper_bgcolor: '#111827', plot_bgcolor: '#111827',
        font: { color: '#e2e8f0' }, margin: { t: 30, b: 40, l: 50, r: 10 },
        xaxis: { title: '时间', rangeslider: { visible: false } },
        yaxis: { title: '价格' }
    }, {responsive: true});
}

function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
}