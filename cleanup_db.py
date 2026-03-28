import sqlite3
from datetime import datetime, timedelta
import config

def cleanup_old_articles():
    # 我們要保留的日期起點：昨天 3/26
    # 今天的日期：3/27
    today = datetime.now()
    yesterday_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # 1. 查找符合條件的文章數量
    cursor.execute("SELECT COUNT(*) FROM articles WHERE published_at < ? AND published_at != ''", (yesterday_str,))
    count = cursor.fetchone()[0]
    
    if count == 0:
        print(f"沒有發現早於 {yesterday_str} 的陳舊文章。")
    else:
        # 2. 執行刪除
        print(f"正在從資料庫中刪除 {count} 篇早於 {yesterday_str} 的陳舊文章...")
        cursor.execute("DELETE FROM articles WHERE published_at < ? AND published_at != ''", (yesterday_str,))
        
        # 3. 也清理一下 monitor_logs (保留最近 30 天)
        month_ago = (today - timedelta(days=30)).isoformat()
        cursor.execute("DELETE FROM monitor_logs WHERE run_at < ?", (month_ago,))
        
        conn.commit()
        print(f"✅ 資料庫清理已完成！已騰出空間並確保 Dashboard 展示數據純淨。")
        
    conn.close()

if __name__ == "__main__":
    cleanup_old_articles()
