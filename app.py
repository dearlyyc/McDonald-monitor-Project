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


@app.route("/api/summaries")
def api_summaries():
    """取得正、負、中立代表性摘要 API"""
    result = database.get_sentiment_summaries()
    return jsonify(result)


# =============================================================================
# 啟動伺服器
# =============================================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
    )
