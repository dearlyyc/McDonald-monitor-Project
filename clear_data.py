import sqlite3
import config
import os

def clear_data():
    db_path = config.DATABASE_PATH
    if not os.path.exists(db_path):
        print(f"找不到資料庫檔案: {db_path}")
        return

    print(f"正在清理資料庫: {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 刪除所有文章資料
        cursor.execute("DELETE FROM articles")
        # 刪除所有執行記錄 (可選，但通常清理時會一起做)
        cursor.execute("DELETE FROM monitor_logs")
        
        # 重設自增 ID (Auto-increment counter)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='articles'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='monitor_logs'")

        conn.commit()
        conn.close()
        print("✅ 成功刪除所有文章資料與執行記錄。")
    except Exception as e:
        print(f"❌ 清理過程中發生錯誤: {e}")

if __name__ == "__main__":
    clear_data()
