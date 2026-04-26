"""
web/app.py - 量化系统 Web 监控面板 (免费版)
从 GitHub Raw 实时读取状态文件，无需本地文件。
"""
from flask import Flask, render_template, jsonify
import requests
import os
import datetime

app = Flask(__name__)

# ❗❗ 请替换为你自己的 GitHub 用户名和仓库名 ❗❗
GITHUB_USER = "你的GitHub用户名"
REPO_NAME = "你的仓库名"          # 比如 quant-ai-system
BRANCH = "main"                 # 如果你的默认分支是 master，就改成 master

def get_raw_url(path):
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{path}"

@app.route("/")
def index():
    return render_template("index.html")

# ======================== 总资产 & 实时状态 ========================
@app.route("/api/status")
def status():
    try:
        r = requests.get(get_raw_url("logs/engine_state.json"), timeout=5)
        if r.status_code != 200:
            return jsonify({})
        state = r.json()
    except:
        state = {}

    cash = state.get("cash", 100000)
    positions = state.get("position", {})
    risk_peak = state.get("risk_peak", cash)
    loss_streak = state.get("loss_streak", 0)

    # 尝试从快照获取总资产，如果没有就用现金估算
    total_asset = cash
    try:
        r2 = requests.get(get_raw_url("logs/performance_snapshots.json"), timeout=5)
        if r2.status_code == 200:
            snapshots = r2.json()
            if snapshots:
                total_asset = snapshots[-1]["total_asset"]
    except:
        pass

    drawdown = (risk_peak - total_asset) / risk_peak if risk_peak else 0
    return jsonify({
        "total_asset": round(total_asset, 2),
        "cash": round(cash, 2),
        "positions": positions,
        "drawdown": round(drawdown, 4),
        "peak_value": round(risk_peak, 2),
        "loss_streak": loss_streak
    })

@app.route("/api/positions")
def positions():
    try:
        r = requests.get(get_raw_url("logs/engine_state.json"), timeout=5)
        if r.status_code == 200:
            data = r.json()
            return jsonify(data.get("position", {}))
    except:
        pass
    return jsonify({})

@app.route("/api/model_weights")
def model_weights():
    try:
        r = requests.get(get_raw_url("logs/engine_state.json"), timeout=5)
        if r.status_code == 200:
            data = r.json()
            return jsonify(data.get("model_weights", {}))
    except:
        pass
    return jsonify({})

@app.route("/api/performance")
def performance():
    summary = {"total_trades": 0, "total_profit": 0, "win_rate": 0}
    snapshots = []
    try:
        r = requests.get(get_raw_url("logs/performance.json"), timeout=5)
        if r.status_code == 200:
            trades = r.json()
            if trades:
                profits = [t.get("profit", 0) for t in trades]
                wins = [p for p in profits if p > 0]
                summary = {
                    "total_trades": len(trades),
                    "total_profit": round(sum(profits), 2),
                    "win_rate": round(len(wins) / len(profits), 4) if profits else 0
                }
    except:
        pass
    try:
        r2 = requests.get(get_raw_url("logs/performance_snapshots.json"), timeout=5)
        if r2.status_code == 200:
            snapshots = r2.json()
    except:
        pass
    return jsonify({"summary": summary, "snapshots": snapshots})

@app.route("/api/history")
def history():
    try:
        r = requests.get(get_raw_url("logs/performance.json"), timeout=5)
        if r.status_code == 200:
            trades = r.json()
            return jsonify(trades[-30:])
    except:
        pass
    return jsonify([])

@app.route("/api/logs")
def logs():
    try:
        r = requests.get(get_raw_url("logs/trading.log"), timeout=5)
        if r.status_code == 200:
            lines = r.text.strip().split('\n')[-100:]
            return jsonify(lines)
    except:
        pass
    return jsonify([])

@app.route("/api/kline/<stock>")
def kline(stock):
    # 生成模拟K线（演示用，可后续接入真实数据）
    import random
    price = 100
    candles = []
    signals = []
    base_time = datetime.datetime.now() - datetime.timedelta(days=30)
    for i in range(30):
        change = random.gauss(0, 1.5)
        open_p = price
        close_p = price + change
        high = max(open_p, close_p) + abs(random.gauss(0, 0.5))
        low = min(open_p, close_p) - abs(random.gauss(0, 0.5))
        t = (base_time + datetime.timedelta(days=i)).isoformat()
        candles.append({
            "time": t, "open": round(open_p,2), "high": round(high,2),
            "low": round(low,2), "close": round(close_p,2)
        })
        if i % 7 == 0:
            signals.append({"type": "buy", "time": t})
        if i % 12 == 0:
            signals.append({"type": "sell", "time": t})
        price = close_p
    return jsonify({"candles": candles, "signals": signals})

if __name__ == "__main__":
    print("🌐 量化监控面板已启动 → http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)