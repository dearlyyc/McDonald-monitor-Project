import sqlite3
import os

source_db = r"D:\OBSIDIAN_Vault\McDonald monitor Project\mcdonalds_monitor.db"
target_db = r"d:\coding projects\McDonald monitor Project\mcdonalds_monitor.db"

def merge_db():
    if not os.path.exists(source_db):
        print(f"找不到備份資料庫: {source_db}")
        return

    s_conn = sqlite3.connect(source_db)
    t_conn = sqlite3.connect(target_db)
    
    s_cursor = s_conn.cursor()
    t_cursor = t_conn.cursor()
    
    # 讀取備份中的所有文章
    print("正在讀取備份中的歷史數據...")
    s_cursor.execute("SELECT * FROM articles")
    articles = s_cursor.fetchall()
    
    # 取得欄位名稱
    col_names = [description[0] for description in s_cursor.description]
    placeholders = ", ".join(["?"] * len(col_names))
    columns = ", ".join(col_names)
    
    inserted_count = 0
    for art in articles:
        # 使用 INSERT OR IGNORE 以免 URL 重複
        try:
            t_cursor.execute(f"INSERT OR IGNORE INTO articles ({columns}) VALUES ({placeholders})", art)
            if t_cursor.rowcount > 0:
                inserted_count += 1
        except Exception as e:
            continue
            
    t_conn.commit()
    print(f"✅ 合併完成！已從 Obsidian 備份中救回 {inserted_count} 筆歷史數據。")
    
    s_conn.close()
    t_conn.close()

if __name__ == "__main__":
    merge_db()
