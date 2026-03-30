import sqlite3
import os
from datetime import datetime, timedelta
import json

DATABASE_PATH = r"d:\coding projects\McDonald monitor Project\mcdonalds_monitor.db"

def diagnose():
    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database not found at {DATABASE_PATH}")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"=== 系統診斷報告 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")

    # 1. 檢查最近 10 筆執行紀錄
    print("\n--- [1] 監控日誌 (monitor_logs) ---")
    try:
        cursor.execute("""
            SELECT run_at, total_collected, total_analyzed, status, error_message 
            FROM monitor_logs 
            ORDER BY run_at DESC LIMIT 10
        """)
        rows = cursor.fetchall()
        if not rows:
            print("警告：沒有發現任何執行日誌！")
        for r in rows:
            print(f"時間: {r['run_at']} | 狀態: {r['status']} | 搜集: {r['total_collected']} | 分析: {r['total_analyzed']}")
            if r['error_message']:
                print(f"   ⚠️ 錯誤: {r['error_message']}")
    except Exception as e:
        print(f"讀取日誌出錯: {e}")

    # 2. 檢查最近的文章數據
    print("\n--- [2] 最近文章數據 ---")
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute("SELECT COUNT(*) FROM articles WHERE analyzed_at LIKE ?", (f"{yesterday_date}%",))
    count_yesterday = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM articles WHERE analyzed_at LIKE ?", (f"{today_date}%",))
    count_today = cursor.fetchone()[0]
    
    print(f"昨日 (3/29) 分析文章數: {count_yesterday}")
    print(f"今日 (3/30) 分析文章數: {count_today}")

    # 3. 檢查最近 5 篇分析完成的文章
    print("\n--- [3] 最新分析存檔 ---")
    cursor.execute("""
        SELECT id, title, source, analyzed_at 
        FROM articles 
        WHERE analyzed_at IS NOT NULL 
        ORDER BY analyzed_at DESC LIMIT 5
    """)
    articles = cursor.fetchall()
    for a in articles:
        print(f"ID: {a['id']} | 分析時間: {a['analyzed_at']} | 來源: {a['source']} | 標題: {a['title'][:40]}")

    conn.close()

if __name__ == "__main__":
    diagnose()
