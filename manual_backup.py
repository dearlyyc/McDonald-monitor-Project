from scheduler import MonitorScheduler
import sys
import os

# 將專案根目錄加入路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def manual_backup():
    print("=" * 50)
    print("📦 手動執行全系統備份 (Backup task)")
    print("=" * 50)
    
    scheduler = MonitorScheduler()
    try:
        scheduler.backup_to_github()
        print("\n" + "=" * 50)
        print("✅ 備份與 GitHub 同步已完成！")
        print("=" * 50)
    except Exception as e:
        print(f"❌ 備份發生錯誤: {e}")

if __name__ == "__main__":
    manual_backup()
