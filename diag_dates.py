import sqlite3
import config
from datetime import datetime, timedelta

def check_dates():
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # 我們要保留的目標日期：昨天 3/26 加上今天 3/27
    target_yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    target_today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"檢查中... (應保留日期: {target_yesterday} 或 {target_today})")
    
    # 查找出版日期不是這兩天的且非空的資料
    cursor.execute("""
        SELECT id, title, published_at, source 
        FROM articles 
        WHERE (published_at NOT LIKE ? AND published_at NOT LIKE ?) 
        AND published_at != ''
    """, (f"{target_yesterday}%", f"{target_today}%"))
    
    rows = cursor.fetchall()
    
    if not rows:
        print("✅ 目前資料庫中沒有不符合日期設定的文章。")
        return
        
    print(f"❌ 發現共 {len(rows)} 篇不符合日期的文章：")
    for row in rows[:20]: # 只列出前 20 篇
        print(f"ID: {row[0]} | Date: {row[2]} | Source: {row[3]} | Title: {row[1]}")
    
    # 詢問刪除邏輯前先暫停或直接刪除
    # ids = [r[0] for r in rows]
    # cursor.execute(f"DELETE FROM articles WHERE id IN ({','.join(map(str, ids))})")
    # conn.commit()
    # print(f"已清理不符設定的文章。")
    conn.close()

if __name__ == "__main__":
    check_dates()
