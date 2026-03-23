import database
import config
import sqlite3
import json

def check():
    database.init_db()
    logs = database.get_recent_logs(5)
    print("=== 最近 5 次監控記錄 ===")
    for l in logs:
        print(f"時間: {l['run_at']} | 搜集: {l['total_collected']} | 分析: {l['total_analyzed']} | 通知: {l['notification_sent']} | 狀態: {l['status']}")
        if l['error_message']:
            print(f"  ❌ 錯誤: {l['error_message'][:100]}")
    
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    print("\n=== 各來源文章數統計環 ===")
    rows = conn.execute("SELECT source, COUNT(*) as cnt, COUNT(analyzed_at) as analyzed_cnt FROM articles GROUP BY source").fetchall()
    for r in rows:
        print(f"來源: {r['source'] or '未知'} | 總數: {r['cnt']} | 已分析: {r['analyzed_cnt']}")
        
    print("\n=== 最近 5 篇分析失敗/未分析文章 ===")
    rows = conn.execute("SELECT source, title, sentiment_reason FROM articles WHERE analyzed_at IS NULL ORDER BY collected_at DESC LIMIT 5").fetchall()
    for r in rows:
        print(f"[{r['source']}] {r['title'][:50]} | 原因: {r['sentiment_reason']}")

    conn.close()

if __name__ == "__main__":
    check()
