"""PRAJNA — Dashboard: Flask-based web interface for real-time monitoring."""

import json
import logging
import numpy as np
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request

logger = logging.getLogger(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PRAJNA — Spacecraft Health Intelligence</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background:#0a0e17; color:#e0e0e0; }
        .header { background:linear-gradient(135deg,#0d1b2a,#1b2838); padding:16px 24px; display:flex; align-items:center; gap:16px; border-bottom:1px solid #1e3a5f; }
        .header h1 { font-size:22px; color:#64ffda; letter-spacing:2px; }
        .header .status { margin-left:auto; padding:6px 14px; border-radius:20px; font-size:13px; font-weight:600; }
        .status-nominal { background:#1b5e20; color:#a5d6a7; }
        .status-watch { background:#e65100; color:#ffcc80; }
        .status-warning { background:#bf360c; color:#ffab91; }
        .status-critical { background:#b71c1c; color:#ef9a9a; animation:pulse 1s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }
        .grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; padding:16px; }
        .card { background:#111b2e; border:1px solid #1e3a5f; border-radius:8px; padding:16px; }
        .card h2 { font-size:14px; color:#64ffda; margin-bottom:12px; text-transform:uppercase; letter-spacing:1px; }
        .full-width { grid-column:1/-1; }
        .node-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:8px; }
        .node-item { background:#0d1b2a; border:1px solid #1e3a5f; border-radius:6px; padding:10px; }
        .node-item .name { font-size:12px; color:#90caf9; margin-bottom:4px; }
        .node-item .score { font-size:20px; font-weight:700; }
        .node-item .bar { height:4px; background:#1e3a5f; border-radius:2px; margin-top:6px; }
        .node-item .bar-fill { height:100%; border-radius:2px; transition:width 0.5s; }
        .score-low { color:#66bb6a; }
        .score-med { color:#ffa726; }
        .score-high { color:#ef5350; }
        .bar-low { background:#66bb6a; }
        .bar-med { background:#ffa726; }
        .bar-high { background:#ef5350; }
        .alert-list { max-height:300px; overflow-y:auto; }
        .alert { padding:8px 12px; border-left:3px solid; margin-bottom:6px; background:#0d1b2a; border-radius:0 4px 4px 0; font-size:13px; }
        .alert-WARNING { border-color:#ffa726; }
        .alert-CRITICAL { border-color:#ef5350; }
        .alert-WATCH { border-color:#42a5f5; }
        .alert .time { color:#78909c; font-size:11px; }
        .kavach-list { list-style:none; }
        .kavach-list li { padding:6px 0; font-size:13px; display:flex; align-items:center; gap:8px; }
        .kavach-pass { color:#66bb6a; }
        .kavach-fail { color:#ef5350; }
        .postflight-table { width:100%; border-collapse:collapse; font-size:13px; }
        .postflight-table th { text-align:left; padding:6px 8px; color:#64ffda; border-bottom:1px solid #1e3a5f; }
        .postflight-table td { padding:6px 8px; border-bottom:1px solid #0d1b2a; }
        .go { color:#66bb6a; } .amber { color:#ffa726; } .reject { color:#ef5350; }
        canvas { max-height:250px; }
        #refreshBtn { background:#1e3a5f; color:#e0e0e0; border:none; padding:8px 16px; border-radius:4px; cursor:pointer; font-size:13px; }
        #refreshBtn:hover { background:#2a4a6f; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛰 PRAJNA</h1>
        <span style="color:#78909c;font-size:13px">Spacecraft Health Intelligence Platform v1.1</span>
        <button id="refreshBtn" onclick="refresh()">↻ Refresh</button>
        <span id="overallStatus" class="status status-nominal">NOMINAL</span>
    </div>
    <div class="grid">
        <div class="card full-width">
            <h2>Subsystem Health — SDWAP Propagated Scores</h2>
            <div class="node-grid" id="nodeGrid"></div>
        </div>
        <div class="card">
            <h2>Score History</h2>
            <canvas id="historyChart"></canvas>
        </div>
        <div class="card">
            <h2>Active Alerts</h2>
            <div class="alert-list" id="alertList"></div>
        </div>
        <div class="card">
            <h2>KAVACH Safety Verification</h2>
            <ul class="kavach-list" id="kavachList"></ul>
        </div>
        <div class="card">
            <h2>Post-Flight Requalification</h2>
            <table class="postflight-table" id="postflightTable">
                <thead><tr><th>Component</th><th>Decision</th><th>Damage</th><th>RUL (flights)</th></tr></thead>
                <tbody></tbody>
            </table>
        </div>
    </div>
    <script>
    const NAMES = ["EPS","TCS","PROP","AOCS","COMM","OBC","PL","STRUCT","HARNESS","PYRO","REA","BATT","SA"];
    let historyChart;
    let scoreHistory = {};
    NAMES.forEach(n => scoreHistory[n] = []);

    function scoreClass(s) { return s > 0.7 ? 'high' : s > 0.4 ? 'med' : 'low'; }

    function renderNodes(data) {
        const grid = document.getElementById('nodeGrid');
        grid.innerHTML = '';
        const scores = data.propagated_scores || data.local_scores || [];
        scores.forEach((s, i) => {
            const cls = scoreClass(s);
            const name = NAMES[i] || 'N'+i;
            scoreHistory[name].push(s);
            if (scoreHistory[name].length > 30) scoreHistory[name].shift();
            grid.innerHTML += `<div class="node-item">
                <div class="name">${name}</div>
                <div class="score score-${cls}">${s.toFixed(3)}</div>
                <div class="bar"><div class="bar-fill bar-${cls}" style="width:${Math.min(s*100,100)}%"></div></div>
            </div>`;
        });
        // Update overall status
        const mx = Math.max(...scores);
        const el = document.getElementById('overallStatus');
        if (mx >= 0.9) { el.textContent='CRITICAL'; el.className='status status-critical'; }
        else if (mx >= 0.7) { el.textContent='WARNING'; el.className='status status-warning'; }
        else if (mx >= 0.5) { el.textContent='WATCH'; el.className='status status-watch'; }
        else { el.textContent='NOMINAL'; el.className='status status-nominal'; }
    }

    function renderAlerts(alerts) {
        const list = document.getElementById('alertList');
        list.innerHTML = '';
        (alerts || []).forEach(a => {
            list.innerHTML += `<div class="alert alert-${a.risk_level}">
                <div>${a.summary}</div>
                <div class="time">${a.timestamp || ''}</div>
            </div>`;
        });
        if (!alerts || alerts.length === 0) list.innerHTML = '<div style="color:#78909c;padding:8px">No active alerts</div>';
    }

    function renderKavach(results) {
        const ul = document.getElementById('kavachList');
        ul.innerHTML = '';
        (results || []).forEach(r => {
            const cls = r.satisfied ? 'kavach-pass' : 'kavach-fail';
            const icon = r.satisfied ? '✅' : '❌';
            ul.innerHTML += `<li class="${cls}">${icon} ${r.property}</li>`;
        });
    }

    function renderPostflight(components) {
        const tbody = document.querySelector('#postflightTable tbody');
        tbody.innerHTML = '';
        (components || []).forEach(c => {
            const cls = c.decision === 'GO' ? 'go' : c.decision === 'AMBER' ? 'amber' : 'reject';
            tbody.innerHTML += `<tr>
                <td>${c.component}</td>
                <td class="${cls}">${c.decision}</td>
                <td>${(c.damage_score||0).toFixed(3)}</td>
                <td>${(c.rul_final||0).toFixed(1)}</td>
            </tr>`;
        });
    }

    function updateChart() {
        const ctx = document.getElementById('historyChart');
        const datasets = NAMES.slice(0,5).map((n,i) => ({
            label: n, data: scoreHistory[n],
            borderColor: ['#ef5350','#ffa726','#66bb6a','#42a5f5','#ab47bc'][i],
            borderWidth: 1.5, fill: false, tension: 0.3, pointRadius: 0,
        }));
        if (historyChart) { historyChart.data.datasets = datasets; historyChart.data.labels = Array.from({length: scoreHistory[NAMES[0]].length}, (_,i)=>i); historyChart.update(); }
        else { historyChart = new Chart(ctx, { type:'line', data:{labels:[], datasets}, options:{animation:false, scales:{y:{min:0,max:1,grid:{color:'#1e3a5f'}},x:{grid:{color:'#1e3a5f'}}}, plugins:{legend:{labels:{color:'#e0e0e0',font:{size:11}}}}}}); }
    }

    async function refresh() {
        try {
            const r = await fetch('/api/state');
            const data = await r.json();
            renderNodes(data);
            renderAlerts(data.alerts);
            renderKavach(data.kavach_results);
            renderPostflight(data.postflight_components);
            updateChart();
        } catch(e) { console.error('Refresh failed:', e); }
    }

    refresh();
    setInterval(refresh, 3000);
    </script>
</body>
</html>
"""


def create_app(pipeline=None):
    """Create the Flask dashboard application.

    Args:
        pipeline: Optional PrajnaPipeline instance for live inference.
                  If None, returns synthetic demo data.

    Returns:
        Flask app
    """
    app = Flask(__name__)
    app.config["pipeline"] = pipeline

    # In-memory state for demo mode
    app.config["demo_step"] = 0

    @app.route("/")
    def index():
        return render_template_string(DASHBOARD_HTML)

    @app.route("/api/state")
    def api_state():
        pip = app.config.get("pipeline")
        if pip and hasattr(pip, "get_current_state"):
            return jsonify(pip.get_current_state())

        # Demo mode — synthetic data
        return jsonify(_generate_demo_state(app))

    @app.route("/api/health")
    def api_health():
        return jsonify({"status": "ok", "version": "1.1.0"})

    return app


def _generate_demo_state(app):
    """Generate synthetic demo state for dashboard visualization."""
    step = app.config.get("demo_step", 0)
    app.config["demo_step"] = step + 1

    np.random.seed(step % 1000)
    N = 13

    # Base scores with occasional anomaly
    base = np.random.exponential(0.1, N).clip(0, 1).astype(float)

    # Inject anomaly patterns every few steps
    if step % 15 < 5:
        fault_node = step % N
        base[fault_node] = 0.6 + np.random.random() * 0.3

    # Simulate SDWAP propagation (simple diffusion)
    propagated = base.copy()
    from prajna.graph import GraphBuilder
    graph = GraphBuilder()
    adj = graph.get_adjacency()
    for _ in range(3):
        propagated = 0.7 * propagated + 0.3 * (adj.T @ propagated)
    propagated = propagated.clip(0, 1)

    # Generate alerts for high scores
    alerts = []
    from prajna.engine.nlg import SUBSYSTEM_NAMES, CONTINGENCY_TEMPLATES
    for i in range(N):
        if propagated[i] > 0.5:
            risk = "CRITICAL" if propagated[i] > 0.9 else "WARNING" if propagated[i] > 0.7 else "WATCH"
            name = SUBSYSTEM_NAMES[i]
            alerts.append({
                "summary": f"[{risk}] {name} anomaly — score {propagated[i]:.3f}",
                "risk_level": risk,
                "timestamp": f"T+{step * 3}s",
            })

    # KAVACH results
    kavach = [
        {"property": "SP-1: Score Bounds", "satisfied": bool(np.all(propagated <= 1.0))},
        {"property": "SP-2: Detector Liveness", "satisfied": True},
        {"property": "SP-3: SDWAP Convergence", "satisfied": True},
        {"property": "SP-4: Prediction Coherence", "satisfied": bool(np.max(propagated) < 0.95)},
        {"property": "SP-5: Requalification Safety", "satisfied": True},
    ]

    # Postflight
    damage = np.random.exponential(0.15, N).clip(0, 1)
    decisions = ["GO" if d < 0.3 else "AMBER" if d < 0.6 else "REJECT" for d in damage]
    postflight = [
        {
            "component": SUBSYSTEM_NAMES[i],
            "decision": decisions[i],
            "damage_score": float(damage[i]),
            "rul_final": float(max(0, 50 - damage[i] * 60)),
        }
        for i in range(N)
    ]

    return {
        "local_scores": base.tolist(),
        "propagated_scores": propagated.tolist(),
        "alerts": alerts,
        "kavach_results": kavach,
        "postflight_components": postflight,
        "step": step,
    }


def run_dashboard(host: str = "127.0.0.1", port: int = 5000, pipeline=None, debug: bool = False):
    """Launch the PRAJNA dashboard server.

    Args:
        host: Bind address
        port: Port number
        pipeline: Optional inference pipeline
        debug: Flask debug mode
    """
    app = create_app(pipeline)
    print(f"🛰  PRAJNA Dashboard: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
