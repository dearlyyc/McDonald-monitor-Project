
from scheduler.jobs import MonitorScheduler
import config
from datetime import datetime

def send_now():
    print(f"[{datetime.now().isoformat()}] 正在啟動手動彙報通知發送流程...")
    
    # 建立排程器實例 (這會讀取 .env 與 config)
    scheduler = MonitorScheduler()
    
    # 執行發送彙報通知的邏輯
    # 注意：此方法會使用分析器產生成綜合摘要
    scheduler.send_daily_summary()
    
    print(f"[{datetime.now().isoformat()}] 發送流程執行結束，請檢查手機端通知。")

if __name__ == "__main__":
    send_now()
