import os
import sqlite3
from datetime import datetime
import config

# 設定要補發的日期
TARGET_DATE = "2026-03-27"

def generate_manual_report():
    print(f" sedang 正在手動為 {TARGET_DATE} 生成缺失的每日報告...")
    
    # 1. 建立目錄
    report_dir = os.path.join(config.OBSIDIAN_VAULT_PATH, "Daily_Reports")
    os.makedirs(report_dir, exist_ok=True)
    
    file_name = f"McDonald_Report_{TARGET_DATE}.md"
    file_path = os.path.join(report_dir, file_name)
    
    # 2. 從資料庫抓取該日期的統計數據
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 統計
    cursor.execute("""
        SELECT sentiment, COUNT(*) as count 
        FROM articles 
        WHERE published_at LIKE ? AND analyzed_at IS NOT NULL
        GROUP BY sentiment
    """, (f"{TARGET_DATE}%",))
    rows = cursor.fetchall()
    stats = {"positive": 0, "negative": 0, "neutral": 0}
    for row in rows:
        if row["sentiment"] in stats:
            stats[row["sentiment"]] = row["count"]
    total = sum(stats.values())
    
    # 負面文章
    cursor.execute("""
        SELECT title, source, url 
        FROM articles 
        WHERE published_at LIKE ? AND sentiment = 'negative'
        ORDER BY analyzed_at DESC LIMIT 10
    """, (f"{TARGET_DATE}%",))
    neg_articles = cursor.fetchall()
    
    conn.close()
    
    # 3. 生成內容
    content = f"""# 🍔 麥當勞輿情報告 - {TARGET_DATE}

## 📊 數據統計
- **總分析篇數**: {total}
- 🟢 **正面**: {stats['positive']}
- 🔴 **負面**: {stats['negative']}
- ⚪ **中立**: {stats['neutral']}

## ⚠️ 負面輿情明細 (前 10 筆)
"""
    if not neg_articles:
        content += "- 該日暫無重大負面消息。\n"
    else:
        for art in neg_articles:
            content += f"- **[{art['source']}]** {art['title']}  \n  [連結]({art['url']})  \n"

    content += f"\n--- \n*本筆記由 McDonald Monitor 系統於 {datetime.now().strftime('%H:%M')} 手動補發生成。*"
    
    # 4. 寫入檔案
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ [OK] 3/27 報告已補發成功：{file_name}")
    print(f"路徑: {file_path}")

if __name__ == "__main__":
    generate_manual_report()
