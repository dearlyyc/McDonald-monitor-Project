
import os
import sys

# 將專案根目錄加入路徑
sys.path.append(os.getcwd())

from scheduler import MonitorScheduler
import database

print("🚀 啟動手動雙重備份程序 (GitHub + Obsidian)...")
database.init_db()
scheduler = MonitorScheduler()

# 執行備份函數
scheduler.backup_to_github()

print("\n✅ 手動備份任務已圓滿完成！")
print("📂 您可以前往 D:\\OBSIDIAN_Vault\\McDonald monitor Project 檢查您的筆記與專案副本。")
