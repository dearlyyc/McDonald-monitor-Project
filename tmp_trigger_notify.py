import sys
import os

# 加入專案路徑
sys.path.append(r"d:\coding projects\McDonald monitor Project")

import config
import database
from scheduler.jobs import MonitorScheduler

def trigger():
    print("--- 正在執行 10:00 排程通知測試 ---")
    scheduler = MonitorScheduler()
    # 手動呼叫發送報告
    scheduler.send_daily_summary()
    print("--- 測試結束 ---")

if __name__ == "__main__":
    trigger()
