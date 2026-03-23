import sqlite3
import config
import os

def check():
    if not os.path.exists(config.DATABASE_PATH):
        print(f"資料庫不存在: {config.DATABASE_PATH}")
        return
        
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    # 統計
    print("=== 各來源統計 ===")
    cursor = conn.execute("SELECT source, COUNT(*) as total, COUNT(analyzed_at) as analyzed FROM articles GROUP BY source")
    for r in cursor:
        print(f"來源: {r['source']:20} | 總數: {r['total']:3} | 已分析: {r['analyzed']:3}")
        
    # 分析失敗原因
    print("\n=== 最近 5 篇未分析文章 ===")
    cursor = conn.execute("SELECT source, title, collected_at FROM articles WHERE analyzed_at IS NULL ORDER BY collected_at DESC LIMIT 5")
    for r in cursor:
        print(f"[{r['source']}] {r['title'][:50]} ({r['collected_at']})")

    # 分析成功但情感異常
    print("\n=== 最近 5 篇分析成功文章 (sentiment_reason) ===")
    cursor = conn.execute("SELECT source, title, sentiment, sentiment_reason FROM articles WHERE analyzed_at IS NOT NULL ORDER BY analyzed_at DESC LIMIT 5")
    for r in cursor:
        print(f"[{r['source']}] {r['title'][:40]} | 情感: {r['sentiment']} | 理由: {r['sentiment_reason']}")

    conn.close()

if __name__ == "__main__":
    check()
