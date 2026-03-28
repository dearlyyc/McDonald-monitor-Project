import sqlite3
import config

def find_2025():
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    # 查找標題或內容提到 2025 或其他往年的關鍵字
    cursor.execute("SELECT id, title, published_at FROM articles WHERE (content LIKE '%2025%' OR title LIKE '%2025%' OR content LIKE '%2024%') AND sentiment = 'negative'")
    rows = cursor.fetchall()
    
    if not rows:
        print("未發現顯性提到 2024/2025 的負面文章。")
        return
        
    for row in rows:
        print(f"ID: {row[0]} | Date: {row[2]} | Title: {row[1]}")
    
    # 刪除這些顯然是過期的負面文章
    ids = [r[0] for r in rows]
    cursor.execute(f"DELETE FROM articles WHERE id IN ({','.join(map(str, ids))})")
    conn.commit()
    print(f"✅ 已刪除 {len(ids)} 篇內容異常的舊負面新聞。")
    conn.close()

if __name__ == "__main__":
    find_2025()
