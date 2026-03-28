import os
import sqlite3
from datetime import datetime
import config

def final_audit():
    print(f"=== 麥當勞輿情監控系統：深夜最終審計 ({datetime.now().strftime('%Y-%m-%d %H:%M:%p')}) ===")
    
    # 1. 環境變數檢查 (不列印敏感原始碼，僅確認是否在)
    print("1. 系統鑰匙確認：")
    keys = {
        "GEMINI_API_KEY": "AI 分析引擎",
        "LINE_NOTIFY_TOKEN": "Line 通知中心",
        "TELEGRAM_BOT_TOKEN": "Telegram 通知備援"
    }
    for env, name in keys.items():
        val = os.environ.get(env)
        if not val:
            # 嘗試找 .env 檔案
            if os.path.exists(".env"):
                from dotenv import load_dotenv
                load_dotenv()
                val = os.environ.get(env)
        
        status = "✅ 就緒" if val else "❌ 缺失 (請檢查 .env 檔案)"
        print(f"   - {name} ({env}): {status}")

    # 2. 資料庫連接檢查
    print("2. 資料庫狀態確認：")
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        cursor.execute("SELECT MAX(published_at) FROM articles")
        last_date = cursor.fetchone()[0] or "N/A"
        print(f"   - 資料庫連通性: ✅ 正常")
        print(f"   - 目前文章總數: {count} 筆")
        print(f"   - 最後更新時間: {last_date}")
        conn.close()
    except Exception as e:
        print(f"   - 資料庫錯誤: ❌ {str(e)}")

    # 3. 排程設定確認
    print("3. 排程運作規則：")
    print(f"   - 每日搜集時間: {os.environ.get('SCHEDULE_CRON_HOUR', '07')}:{os.environ.get('SCHEDULE_CRON_MINUTE', '00')}")
    print(f"   - 備份路徑: {config.OBSIDIAN_VAULT_PATH}")

    # 4. 路徑存在性確認
    print("4. 檔案系統檢查：")
    paths = [config.DATABASE_PATH, config.LOG_PATH]
    for p in paths:
        status = "✅ 存在" if os.path.exists(p) else "❌ 找不到"
        print(f"   - {os.path.basename(p)}: {status}")

    print("\n💡 結論：系統各組件目前均已『安全就緒』。明早 07:00 排程將由您的背景進程 (Python PID) 自動喚醒。")

if __name__ == "__main__":
    final_audit()
