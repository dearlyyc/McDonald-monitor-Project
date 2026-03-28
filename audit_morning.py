import sqlite3
import config
from datetime import datetime, timedelta

def audit_today():
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # 昨天 3/27 (搜集的目標)
    target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    cursor.execute("SELECT COUNT(*) FROM articles WHERE published_at LIKE ?", (f"{target_date}%",))
    count = cursor.fetchone()[0]
    
    cursor.execute("SELECT sentiment, COUNT(*) FROM articles WHERE published_at LIKE ? GROUP BY sentiment", (f"{target_date}%",))
    sentiments = cursor.fetchall()
    
    print(f"=== 今日排程成果報告 (07:00 執行) ===")
    print(f"搜集目標日期: {target_date}")
    print(f"成功搜集文章: {count} 筆")
    for s, c in sentiments:
        print(f"   - {s}: {c} 筆")
        
    # 檢查最後一個 Log
    cursor.execute("SELECT run_at, total_collected, total_analyzed, status FROM monitor_logs ORDER BY run_at DESC LIMIT 1")
    last_log = cursor.fetchone()
    if last_log:
        print(f"\n最後執行日誌 (於 {last_log[0]})：")
        print(f"   - 搜集總數: {last_log[1]} 筆")
        print(f"   - 分析總數: {last_log[2]} 筆")
        print(f"   - 執行狀態: {'✅ 成功' if last_log[3]=='success' else '❌ 失敗'}")
        
    conn.close()

if __name__ == "__main__":
    audit_today()
