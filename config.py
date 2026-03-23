"""
麥當勞品牌輿情監控系統 - 設定檔
"""
import os
from dotenv import load_dotenv

# 讀取 .env 檔案
load_dotenv()

# =============================================================================
# 搜集設定
# =============================================================================
# 搜集關鍵字
SEARCH_KEYWORDS = ["麥當勞", "McDonald's", "McDonalds", "麥當勞 活動", "麥當勞 優惠"]

# Google News RSS 語言與地區
GOOGLE_NEWS_LANG = "zh-TW"
GOOGLE_NEWS_REGION = "TW"

# PTT 看板
PTT_BOARDS = ["Gossiping", "fastfood", "Lifeismoney"]

# Dcard 看板
DCARD_FORUMS = ["food", "trending", "funny"]

# Facebook 粉絲頁（搜集公開貼文）
FACEBOOK_PAGES = ["McDonalds", "McDonaldsTaiwan"]

# Instagram 帳號
INSTAGRAM_ACCOUNTS = ["mcdonalds", "mcdonaldstw"]

# Google Maps 地點（用於評論搜集）
GOOGLE_PLACES_KEYWORDS = ["麥當勞"]

# Tavily API 授權金鑰
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# Apify API 授權金鑰
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")

# =============================================================================
# LLM 分析設定
# =============================================================================
# LLM 提供商：'openai' 或 'gemini'
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")

# OpenAI 設定
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"

# Google Gemini 設定
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"

# =============================================================================
# 通知設定
# =============================================================================
# Line Notify
LINE_NOTIFY_TOKEN = os.environ.get("LINE_NOTIFY_TOKEN", "")

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# 通知觸發條件：出現負面新聞時通知
NOTIFY_ON_NEGATIVE = True
# 每次排程完成後發送摘要
NOTIFY_SUMMARY = True

# =============================================================================
# 排程設定
# =============================================================================
# 排程模式：'cron'（定時）或 'interval'（間隔）
SCHEDULE_MODE = os.environ.get("SCHEDULE_MODE", "cron")

# Cron 模式設定 — 每天早上 7 點執行
SCHEDULE_CRON_HOUR = int(os.environ.get("SCHEDULE_CRON_HOUR", "7"))
SCHEDULE_CRON_MINUTE = int(os.environ.get("SCHEDULE_CRON_MINUTE", "0"))

# Interval 模式設定（備用）
SCHEDULE_INTERVAL_HOURS = int(os.environ.get("SCHEDULE_INTERVAL_HOURS", "24"))

# =============================================================================
# 資料庫設定
# =============================================================================
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcdonalds_monitor.db")

# =============================================================================
# Flask 設定
# =============================================================================
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True
SECRET_KEY = os.environ.get("SECRET_KEY", "mcdonalds-monitor-secret-key-change-me")
APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:5000")

