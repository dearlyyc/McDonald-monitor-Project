import sqlite3
import config
from datetime import datetime

def check_ui_stats():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"查詢今日 ({today}) 的統計...")
    
    # 模仿 get_sentiment_stats(1) 的邏輯
    cursor.execute("""
        SELECT sentiment, COUNT(*) as count 
        FROM articles 
        WHERE analyzed_at >= ? AND analyzed_at IS NOT NULL
        GROUP BY sentiment
    """, (today,))
    
    rows = cursor.fetchall()
    stats = {"positive": 0, "negative": 0, "neutral": 0}
    for row in rows:
        print(f"發現 {row['sentiment']}: {row['count']} 筆")
        if row["sentiment"] in stats:
            stats[row["sentiment"]] = row["count"]
            
    print(f"總結: {stats}")
    
    # 檢查是否有文章被分析但分析時間被誤設了？
    cursor.execute("SELECT id, title, analyzed_at FROM articles ORDER BY analyzed_at DESC LIMIT 5")
    latest = cursor.fetchall()
    print("\n最新分析的 5 篇文章：")
    for r in latest:
        print(f"ID: {r['id']} | Ana: {r['analyzed_at']} | Title: {r['title']}")
        
    conn.close()

if __name__ == "__main__":
    check_ui_stats()
