"""
麥當勞品牌輿情監控系統 - Flask 主程式
"""
from flask import Flask, render_template, jsonify, request
import atexit

import config
import database
from scheduler import MonitorScheduler

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# 初始化資料庫
database.init_db()

# 初始化排程器
monitor_scheduler = MonitorScheduler()
monitor_scheduler.start()
atexit.register(monitor_scheduler.stop)


# =============================================================================
# 頁面路由
# =============================================================================

@app.route("/")
def index():
    """主報告頁面"""
    return render_template("index.html")


# =============================================================================
# API 路由
# =============================================================================

@app.route("/api/articles")
def api_articles():
    """取得文章列表 API"""
    sentiment = request.args.get("sentiment", "all")
    source = request.args.get("source", "all")
    days = int(request.args.get("days", 7))
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    result = database.get_articles(
        sentiment=sentiment,
        source=source,
        days=days,
        page=page,
        per_page=per_page,
    )
    return jsonify(result)


@app.route("/api/stats")
def api_stats():
    """取得情感統計 API"""
    days = int(request.args.get("days", 7))
    stats = database.get_sentiment_stats(days=days)
    return jsonify(stats)


@app.route("/api/source-stats")
def api_source_stats():
    """取得來源統計 API"""
    days = int(request.args.get("days", 7))
    stats = database.get_source_stats(days=days)
    return jsonify(stats)


@app.route("/api/daily-stats")
def api_daily_stats():
    """取得每日統計 API（圖表用）"""
    days = int(request.args.get("days", 30))
    data = database.get_daily_stats(days=days)
    return jsonify(data)


@app.route("/api/logs")
def api_logs():
    """取得監控執行記錄 API"""
    limit = int(request.args.get("limit", 10))
    logs = database.get_recent_logs(limit=limit)
    return jsonify(logs)


@app.route("/api/run-now", methods=["POST"])
def api_run_now():
    """立即執行一次監控週期 (非同步)"""
    import threading
    if monitor_scheduler.is_running:
        return jsonify({"status": "running", "message": "監控週期正在執行中"}), 400
    
    # 使用 Thread 在背景執行
    thread = threading.Thread(target=monitor_scheduler.run_monitor_cycle)
    thread.start()
    
    return jsonify({"status": "success", "message": "已在背景啟動監控週期"})


@app.route("/api/run-status")
def api_run_status():
    """取得目前的執行狀態"""
    return jsonify({
        "is_running": monitor_scheduler.is_running
    })


if __name__ == "__main__":
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
    )
