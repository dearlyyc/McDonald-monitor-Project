from scheduler import MonitorScheduler
import sys
import os

# 將專案根目錄加入路徑 (確保能正確匯入 modules)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def manual_run():
    print("=" * 50)
    print("🚀 手動觸發補遺監控任務 (Manual Run)")
    print("=" * 50)
    
    scheduler = MonitorScheduler()
    # 執行完整監控週期，包括：搜集、分析、並發送通知
    # notify=True 表示作業完成後會發送 Line/Telegram 通知
    try:
        log = scheduler.run_monitor_cycle(notify=True)
        if log:
            print("\n" + "=" * 50)
            print("✅ 任務已完成！")
            print(f"📊 搜集篇數: {log.get('total_collected', 0)}")
            print(f"🔬 分析篇數: {log.get('total_analyzed', 0)}")
            print(f"🔔 通知狀態: {'已發送' if log.get('status') == 'success' else '失敗'}")
            print("=" * 50)
    except Exception as e:
        print(f"❌ 執行發生錯誤: {e}")

if __name__ == "__main__":
    manual_run()
