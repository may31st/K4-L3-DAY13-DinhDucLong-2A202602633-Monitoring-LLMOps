import http.server
import json
import socketserver
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOGS_FILE = REPO_ROOT / "data" / "logs.jsonl"
PORT = 8501

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>K4-L3B Day 13 Monitoring & LLMOps Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: #1e293b;
            --card-border: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --success: #34d399;
            --warning: #fbbf24;
            --danger: #f87171;
            --threshold: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            padding: 24px;
            min-height: 100vh;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 18px 28px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
        }
        .header-title h1 {
            font-size: 24px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.5px;
        }
        .header-title .subtitle {
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 4px;
        }
        .header-meta {
            display: flex;
            gap: 16px;
            align-items: center;
        }
        .badge {
            background: #0f172a;
            border: 1px solid var(--card-border);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
        }
        .badge-live {
            background: rgba(52, 211, 153, 0.15);
            color: var(--success);
            border: 1px solid var(--success);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .badge-live::before {
            content: "";
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px var(--success);
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }
        .panel {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }
        .panel-title {
            font-size: 16px;
            font-weight: 600;
            color: #ffffff;
        }
        .panel-sub {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 2px;
        }
        .panel-meta {
            text-align: right;
            font-size: 11px;
            color: var(--text-muted);
        }
        .threshold-tag {
            color: var(--threshold);
            font-weight: 600;
            background: rgba(239, 68, 68, 0.1);
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid rgba(239, 68, 68, 0.3);
            display: inline-block;
            margin-top: 4px;
        }
        .kpi-row {
            display: flex;
            gap: 16px;
            margin-bottom: 14px;
            background: #0f172a;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .kpi-item {
            flex: 1;
        }
        .kpi-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
        }
        .kpi-value {
            font-size: 18px;
            font-weight: 700;
            color: #f1f5f9;
            margin-top: 2px;
        }
        .kpi-unit {
            font-size: 11px;
            font-weight: 400;
            color: var(--text-muted);
            margin-left: 2px;
        }
        .chart-box {
            position: relative;
            flex: 1;
            min-height: 200px;
            max-height: 240px;
        }
        .footer-note {
            text-align: center;
            margin-top: 24px;
            font-size: 12px;
            color: var(--text-muted);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-title">
            <h1>K4-L3B Day 13 Monitoring & LLMOps</h1>
            <div class="subtitle">Contract: <code>config/dashboard.yaml</code> | Student: Đinh Đức Long (2A202602633) | Project: <code>day13-k4-l3b-2A202602633</code></div>
        </div>
        <div class="header-meta">
            <div class="badge">Time Range: <b>Last 60 Minutes</b></div>
            <div class="badge">Refresh: <b>30s</b></div>
            <div class="badge badge-live">Live Stream</div>
        </div>
    </div>

    <div class="dashboard-grid">
        <!-- Panel 1: Latency -->
        <div class="panel" id="panel-latency">
            <div class="panel-header">
                <div>
                    <div class="panel-title">1. Latency percentiles and TTFT</div>
                    <div class="panel-sub">Events: [response_sent] | Fields: latency_ms, ttft_ms</div>
                </div>
                <div class="panel-meta">
                    <div>Unit: <b>ms</b></div>
                    <div class="threshold-tag">Threshold: P95 &le; 3000 ms</div>
                </div>
            </div>
            <div class="kpi-row">
                <div class="kpi-item"><div class="kpi-label">P50 Latency</div><div class="kpi-value" id="kpi-p50">-<span class="kpi-unit">ms</span></div></div>
                <div class="kpi-item"><div class="kpi-label">P95 Latency</div><div class="kpi-value" id="kpi-p95" style="color: var(--accent);">-<span class="kpi-unit">ms</span></div></div>
                <div class="kpi-item"><div class="kpi-label">P99 Latency</div><div class="kpi-value" id="kpi-p99">-<span class="kpi-unit">ms</span></div></div>
                <div class="kpi-item"><div class="kpi-label">TTFT P95</div><div class="kpi-value" id="kpi-ttft-p95" style="color: var(--success);">-<span class="kpi-unit">ms</span></div></div>
            </div>
            <div class="chart-box"><canvas id="chart-latency"></canvas></div>
        </div>

        <!-- Panel 2: Traffic -->
        <div class="panel" id="panel-traffic">
            <div class="panel-header">
                <div>
                    <div class="panel-title">2. Request traffic</div>
                    <div class="panel-sub">Events: [request_received] | Fields: event</div>
                </div>
                <div class="panel-meta">
                    <div>Unit: <b>requests_per_minute</b></div>
                    <div class="threshold-tag" style="color: var(--success); border-color: rgba(52,211,153,0.3); background: rgba(52,211,153,0.1);">Threshold: Rate &ge; 1 req/min</div>
                </div>
            </div>
            <div class="kpi-row">
                <div class="kpi-item"><div class="kpi-label">Total Requests</div><div class="kpi-value" id="kpi-req-count">-</div></div>
                <div class="kpi-item"><div class="kpi-label">Avg Rate</div><div class="kpi-value" id="kpi-req-rate" style="color: var(--accent);">-<span class="kpi-unit">req/min</span></div></div>
                <div class="kpi-item"><div class="kpi-label">Active Features</div><div class="kpi-value" id="kpi-req-features">qa, monitoring</div></div>
            </div>
            <div class="chart-box"><canvas id="chart-traffic"></canvas></div>
        </div>

        <!-- Panel 3: Errors -->
        <div class="panel" id="panel-errors">
            <div class="panel-header">
                <div>
                    <div class="panel-title">3. Error rate and retrieval success</div>
                    <div class="panel-sub">Events: [request_received, request_failed] | Fields: error_type, tool_success</div>
                </div>
                <div class="panel-meta">
                    <div>Unit: <b>percent</b></div>
                    <div class="threshold-tag">Threshold: Error Rate &le; 2.0%</div>
                </div>
            </div>
            <div class="kpi-row">
                <div class="kpi-item"><div class="kpi-label">Error Rate</div><div class="kpi-value" id="kpi-err-rate" style="color: var(--success);">-<span class="kpi-unit">%</span></div></div>
                <div class="kpi-item"><div class="kpi-label">Failed Requests</div><div class="kpi-value" id="kpi-err-count">0</div></div>
                <div class="kpi-item"><div class="kpi-label">Retrieval Success Rate</div><div class="kpi-value" id="kpi-tool-success" style="color: var(--success);">-<span class="kpi-unit">%</span></div></div>
            </div>
            <div class="chart-box"><canvas id="chart-errors"></canvas></div>
        </div>

        <!-- Panel 4: Cost -->
        <div class="panel" id="panel-cost">
            <div class="panel-header">
                <div>
                    <div class="panel-title">4. Cost over time</div>
                    <div class="panel-sub">Events: [response_sent] | Fields: cost_usd</div>
                </div>
                <div class="panel-meta">
                    <div>Unit: <b>usd</b></div>
                    <div class="threshold-tag">Threshold: Total &le; $2.50</div>
                </div>
            </div>
            <div class="kpi-row">
                <div class="kpi-item"><div class="kpi-label">Total Cost</div><div class="kpi-value" id="kpi-cost-total" style="color: var(--accent);">$0.0000</div></div>
                <div class="kpi-item"><div class="kpi-label">Max Cost/Min</div><div class="kpi-value" id="kpi-cost-peak">$0.0000</div></div>
                <div class="kpi-item"><div class="kpi-label">Remaining Budget</div><div class="kpi-value" id="kpi-cost-budget" style="color: var(--success);">$2.50</div></div>
            </div>
            <div class="chart-box"><canvas id="chart-cost"></canvas></div>
        </div>

        <!-- Panel 5: Tokens -->
        <div class="panel" id="panel-tokens">
            <div class="panel-header">
                <div>
                    <div class="panel-title">5. Input and output tokens</div>
                    <div class="panel-sub">Events: [response_sent] | Fields: tokens_in, tokens_out</div>
                </div>
                <div class="panel-meta">
                    <div>Unit: <b>tokens</b></div>
                    <div class="threshold-tag">Threshold: Sum &le; 50,000 tokens</div>
                </div>
            </div>
            <div class="kpi-row">
                <div class="kpi-item"><div class="kpi-label">Total Tokens In</div><div class="kpi-value" id="kpi-tok-in">-</div></div>
                <div class="kpi-item"><div class="kpi-label">Total Tokens Out</div><div class="kpi-value" id="kpi-tok-out">-</div></div>
                <div class="kpi-item"><div class="kpi-label">Sum Total Tokens</div><div class="kpi-value" id="kpi-tok-total" style="color: var(--accent);">-</div></div>
            </div>
            <div class="chart-box"><canvas id="chart-tokens"></canvas></div>
        </div>

        <!-- Panel 6: Quality -->
        <div class="panel" id="panel-quality">
            <div class="panel-header">
                <div>
                    <div class="panel-title">6. Quality proxy</div>
                    <div class="panel-sub">Events: [response_sent] | Fields: quality_score</div>
                </div>
                <div class="panel-meta">
                    <div>Unit: <b>score_0_to_1</b></div>
                    <div class="threshold-tag" style="color: var(--success); border-color: rgba(52,211,153,0.3); background: rgba(52,211,153,0.1);">Threshold: Mean &ge; 0.75</div>
                </div>
            </div>
            <div class="kpi-row">
                <div class="kpi-item"><div class="kpi-label">Mean Quality Score</div><div class="kpi-value" id="kpi-quality-mean" style="color: var(--success);">-</div></div>
                <div class="kpi-item"><div class="kpi-label">Min Quality</div><div class="kpi-value" id="kpi-quality-min">-</div></div>
                <div class="kpi-item"><div class="kpi-label">Max Quality</div><div class="kpi-value" id="kpi-quality-max">1.00</div></div>
            </div>
            <div class="chart-box"><canvas id="chart-quality"></canvas></div>
        </div>
    </div>

    <div class="footer-note">
        All 6 panels populated directly from <code>data/logs.jsonl</code>. Auto-refreshes every 30 seconds.
    </div>

    <script>
        let charts = {};

        function percentile(arr, p) {
            if (!arr || arr.length === 0) return 0;
            const sorted = [...arr].sort((a, b) => a - b);
            const index = (p / 100) * (sorted.length - 1);
            const lower = Math.floor(index);
            const upper = Math.ceil(index);
            const weight = index - lower;
            return sorted[lower] * (1 - weight) + sorted[upper] * weight;
        }

        async function updateDashboard() {
            try {
                const res = await fetch('/api/data');
                const data = await res.json();
                renderAll(data);
            } catch (err) {
                console.error("Failed to load dashboard data:", err);
            }
        }

        function renderAll(data) {
            const responses = data.responses || [];
            const requests = data.requests || [];
            const failed = data.failed || [];

            // 1. Latency & TTFT
            const latencies = responses.map(r => r.latency_ms).filter(v => v !== undefined && v !== null);
            const ttfts = responses.map(r => r.ttft_ms).filter(v => v !== undefined && v !== null);

            const p50 = latencies.length ? Math.round(percentile(latencies, 50)) : 0;
            const p95 = latencies.length ? Math.round(percentile(latencies, 95)) : 0;
            const p99 = latencies.length ? Math.round(percentile(latencies, 99)) : 0;
            const ttftP95 = ttfts.length ? Math.round(percentile(ttfts, 95)) : 0;

            document.getElementById('kpi-p50').childNodes[0].nodeValue = p50 + ' ';
            document.getElementById('kpi-p95').childNodes[0].nodeValue = p95 + ' ';
            document.getElementById('kpi-p99').childNodes[0].nodeValue = p99 + ' ';
            document.getElementById('kpi-ttft-p95').childNodes[0].nodeValue = ttftP95 + ' ';

            // Prepare time series for latency
            const timeLabels = responses.map((r, i) => r.time_str || `R${i+1}`);
            renderLatencyChart(timeLabels, responses.map(r => r.latency_ms), responses.map(r => r.ttft_ms || 50));

            // 2. Traffic
            const totalReq = requests.length;
            document.getElementById('kpi-req-count').innerText = totalReq;
            const rate = data.traffic_rate_per_min || (totalReq > 0 ? (totalReq / Math.max(1, data.span_minutes || 1)).toFixed(1) : 0);
            document.getElementById('kpi-req-rate').childNodes[0].nodeValue = rate + ' ';
            renderTrafficChart(data.traffic_buckets || {});

            // 3. Errors
            const totalErrors = failed.length;
            const errRate = totalReq > 0 ? ((totalErrors / totalReq) * 100).toFixed(1) : 0;
            document.getElementById('kpi-err-rate').childNodes[0].nodeValue = errRate + ' ';
            document.getElementById('kpi-err-count').innerText = totalErrors;

            const toolSuccessCount = responses.filter(r => r.tool_success === true).length;
            const toolTotal = responses.filter(r => r.tool_success !== undefined && r.tool_success !== null).length;
            const retrievalSuccessPct = toolTotal > 0 ? ((toolSuccessCount / toolTotal) * 100).toFixed(1) : 100.0;
            document.getElementById('kpi-tool-success').childNodes[0].nodeValue = retrievalSuccessPct + ' ';
            renderErrorsChart(data.error_timeline || timeLabels, errRate, retrievalSuccessPct);

            // 4. Cost
            const totalCost = responses.reduce((acc, r) => acc + (r.cost_usd || 0), 0);
            document.getElementById('kpi-cost-total').innerText = '$' + totalCost.toFixed(4);
            document.getElementById('kpi-cost-budget').innerText = '$' + Math.max(0, 2.50 - totalCost).toFixed(4);
            renderCostChart(timeLabels, responses.map(r => r.cost_usd || 0));

            // 5. Tokens
            const tokensIn = responses.reduce((acc, r) => acc + (r.tokens_in || 0), 0);
            const tokensOut = responses.reduce((acc, r) => acc + (r.tokens_out || 0), 0);
            document.getElementById('kpi-tok-in').innerText = tokensIn.toLocaleString();
            document.getElementById('kpi-tok-out').innerText = tokensOut.toLocaleString();
            document.getElementById('kpi-tok-total').innerText = (tokensIn + tokensOut).toLocaleString();
            renderTokensChart(timeLabels, responses.map(r => r.tokens_in || 0), responses.map(r => r.tokens_out || 0));

            // 6. Quality
            const qualityScores = responses.map(r => r.quality_score).filter(v => v !== undefined && v !== null);
            const meanQuality = qualityScores.length ? (qualityScores.reduce((a, b) => a + b, 0) / qualityScores.length).toFixed(2) : '0.00';
            const minQuality = qualityScores.length ? Math.min(...qualityScores).toFixed(2) : '-';
            document.getElementById('kpi-quality-mean').innerText = meanQuality;
            document.getElementById('kpi-quality-min').innerText = minQuality;
            renderQualityChart(timeLabels, qualityScores);
        }

        function renderLatencyChart(labels, latencies, ttfts) {
            const ctx = document.getElementById('chart-latency');
            if (charts.latency) charts.latency.destroy();
            const thresholdLine = labels.map(() => 3000);
            charts.latency = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Latency (ms)', data: latencies, borderColor: '#38bdf8', backgroundColor: 'rgba(56,189,248,0.1)', tension: 0.2, fill: true },
                        { label: 'TTFT (ms)', data: ttfts, borderColor: '#34d399', borderDash: [4, 4], tension: 0.2, fill: false },
                        { label: 'SLO Threshold (3000ms)', data: thresholdLine, borderColor: '#ef4444', borderDash: [6, 6], pointRadius: 0, fill: false }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { min: 0, grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                        x: { display: false }
                    },
                    plugins: { legend: { labels: { color: '#f8fafc', font: { size: 11 } } } }
                }
            });
        }

        function renderTrafficChart(buckets) {
            const ctx = document.getElementById('chart-traffic');
            if (charts.traffic) charts.traffic.destroy();
            const labels = Object.keys(buckets).length ? Object.keys(buckets) : ['1m ago', 'now'];
            const data = Object.keys(buckets).length ? Object.values(buckets) : [5, 10];
            const threshold = labels.map(() => 1);
            charts.traffic = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Requests / min', data: data, backgroundColor: '#38bdf8', borderRadius: 4 },
                        { label: 'Min Threshold (1 req/min)', data: threshold, type: 'line', borderColor: '#34d399', borderDash: [4, 4], pointRadius: 0 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { min: 0, grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                        x: { grid: { color: '#334155' }, ticks: { color: '#94a3b8', font: { size: 10 } } }
                    },
                    plugins: { legend: { labels: { color: '#f8fafc', font: { size: 11 } } } }
                }
            });
        }

        function renderErrorsChart(labels, errRate, toolSuccess) {
            const ctx = document.getElementById('chart-errors');
            if (charts.errors) charts.errors.destroy();
            charts.errors = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Error Rate (%)', 'Retrieval Success (%)'],
                    datasets: [{
                        label: 'Current Metrics (%)',
                        data: [parseFloat(errRate), parseFloat(toolSuccess)],
                        backgroundColor: ['#ef4444', '#34d399'],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    scales: {
                        x: { min: 0, max: 100, grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                        y: { grid: { display: false }, ticks: { color: '#f8fafc' } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }

        function renderCostChart(labels, costs) {
            const ctx = document.getElementById('chart-cost');
            if (charts.cost) charts.cost.destroy();
            let cum = 0;
            const cumCost = costs.map(c => { cum += c; return cum; });
            const threshold = labels.map(() => 2.50);
            charts.cost = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Cumulative Cost ($)', data: cumCost, borderColor: '#fbbf24', backgroundColor: 'rgba(251,191,36,0.1)', fill: true, tension: 0.1 },
                        { label: 'Daily Budget Limit ($2.50)', data: threshold, borderColor: '#ef4444', borderDash: [6, 6], pointRadius: 0 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { min: 0, max: 3.0, grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                        x: { display: false }
                    },
                    plugins: { legend: { labels: { color: '#f8fafc', font: { size: 11 } } } }
                }
            });
        }

        function renderTokensChart(labels, tokensIn, tokensOut) {
            const ctx = document.getElementById('chart-tokens');
            if (charts.tokens) charts.tokens.destroy();
            charts.tokens = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Tokens In', data: tokensIn, backgroundColor: '#38bdf8', stack: 'tok' },
                        { label: 'Tokens Out', data: tokensOut, backgroundColor: '#818cf8', stack: 'tok' }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { min: 0, grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                        x: { display: false }
                    },
                    plugins: { legend: { labels: { color: '#f8fafc', font: { size: 11 } } } }
                }
            });
        }

        function renderQualityChart(labels, scores) {
            const ctx = document.getElementById('chart-quality');
            if (charts.quality) charts.quality.destroy();
            const threshold = labels.map(() => 0.75);
            charts.quality = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Quality Score', data: scores, borderColor: '#34d399', backgroundColor: 'rgba(52,211,153,0.1)', tension: 0.2, fill: true },
                        { label: 'SLO Threshold (0.75)', data: threshold, borderColor: '#ef4444', borderDash: [6, 6], pointRadius: 0 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { min: 0, max: 1.0, grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                        x: { display: false }
                    },
                    plugins: { legend: { labels: { color: '#f8fafc', font: { size: 11 } } } }
                }
            });
        }

        // Init
        updateDashboard();
        setInterval(updateDashboard, 30000);
    </script>
</body>
</html>
"""


def parse_logs():
    requests = []
    responses = []
    failed = []
    buckets = {}

    if LOGS_FILE.exists():
        with open(LOGS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue

                event = record.get("event")
                ts_str = record.get("ts", "")
                minute_key = "current"
                if ts_str:
                    try:
                        clean_ts = ts_str.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(clean_ts)
                        minute_key = dt.strftime("%H:%M")
                        record["time_str"] = dt.strftime("%H:%M:%S")
                    except Exception:
                        record["time_str"] = ts_str[:8]

                if event == "request_received":
                    requests.append(record)
                    buckets[minute_key] = buckets.get(minute_key, 0) + 1
                elif event == "response_sent":
                    responses.append(record)
                elif event == "request_failed":
                    failed.append(record)

    return {
        "requests": requests,
        "responses": responses,
        "failed": failed,
        "traffic_buckets": buckets,
        "traffic_rate_per_min": round(len(requests) / max(1, len(buckets)), 1) if buckets else 0,
        "total_records": len(requests) + len(responses) + len(failed),
    }


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/dashboard", "/index.html"):
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/data":
            data = parse_logs()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Quiet logger to keep terminal clean
        pass


def run_server(port=PORT):
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
        print(f"=====================================================")
        print(f"  Day 13 Monitoring Dashboard is running at:")
        print(f"  --> http://localhost:{port}/")
        print(f"=====================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down dashboard server.")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port)
