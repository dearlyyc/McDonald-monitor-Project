import os
import sqlite3
import json
from datetime import datetime, timedelta

def get_db_connection():
    conn = sqlite3.connect('mcdonalds_monitor.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_report(date_str):
    print(f"Generating report for {date_str}...")
    conn = get_db_connection()
    
    # Get the latest log entry for this date
    log = conn.execute("SELECT * FROM monitor_logs WHERE run_at LIKE ? ORDER BY run_at DESC LIMIT 1", (f"{date_str}%",)).fetchone()
    
    if not log:
        print(f"  [Skip] No monitor logs found for {date_str}.")
        conn.close()
        return

    # Get negative articles for that date
    # Note: analyzed_at or collected_at should be on that date.
    # To be safe, we check for articles analyzed on that date.
    rows = conn.execute("""
        SELECT source, title, url 
        FROM articles 
        WHERE sentiment = 'negative' 
        AND analyzed_at LIKE ? 
        ORDER BY analyzed_at DESC 
        LIMIT 10
    """, (f"{date_str}%",)).fetchall()
    
    obsidian_path = r"D:\OBSIDIAN_Vault\McDonald monitor Project\Daily_Reports"
    if not os.path.exists(obsidian_path):
        os.makedirs(obsidian_path, exist_ok=True)
        
    file_name = f"McDonald_Report_{date_str}.md"
    file_path = os.path.join(obsidian_path, file_name)
    
    content = f"""# 🍔 麥當勞輿情報告 - {date_str}

## 📊 數據統計
- **總搜集篇數**: {log['total_collected']}
- 🟢 **正面**: {log['positive_count']}
- 🔴 **負面**: {log['negative_count']}
- ⚪ **中立**: {log['neutral_count']}

## ⚠️ 今日負面關注
"""
    if not rows:
        content += "- 當日暫無重大負面消息。\n"
    else:
        for row in rows:
            content += f"- **[{row['source']}]** {row['title']}  \n  [連結]({row['url']})  \n"

    content += f"\n--- \n*本筆記由 McDonald Monitor 系統於 {datetime.now().strftime('%H:%M')} 手動補遺生成。*"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [OK] 報告已存至 Obsidian: {file_name}")
    conn.close()

if __name__ == "__main__":
    # Generate for 3/25
    generate_report("2026-03-25")
    # Also generate for 3/26 if the run is finished
    generate_report("2026-03-26")
