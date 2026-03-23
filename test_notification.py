import config
from notifier.line_notify import LineNotifier
from notifier.telegram_notify import TelegramNotifier

def test_notification():
    print(f"正在使用網址測試通知: {config.APP_URL}")
    
    # 建立模擬數據
    stats = {
        "total": 100,
        "positive": 10,
        "negative": 5,
        "neutral": 85
    }
    
    negative_articles = [
        {"title": "測試：麥當勞服務生態度不佳"},
        {"title": "測試：大麥克裡面有頭髮"},
        {"title": "測試：薯條不夠熱"}
    ]
    
    trend_stats = {
        "diff_negative": 2,
        "diff_positive": -1
    }
    
    ai_summary = "這是一封來自「麥當勞輿情監控系統」的測試通知。旨在確認 Cloudflare Tunnel 網址是否能正確在您的行動網路環境中開啟。"

    # 1. 測試 Line Notify
    line = LineNotifier()
    if line.is_configured:
        print("正在發送 Line 測試通知...")
        line.send_summary(
            stats=stats,
            negative_articles=negative_articles,
            trend_stats=trend_stats,
            ai_summary=ai_summary
        )
    else:
        print("跳過 Line 通知 (未設定 Token)")

    # 2. 測試 Telegram
    tg = TelegramNotifier()
    if tg.is_configured:
        print("正在發送 Telegram 測試通知...")
        tg.send_summary(
            stats=stats,
            negative_articles=negative_articles,
            trend_stats=trend_stats,
            ai_summary=ai_summary
        )
    else:
        print("跳過 Telegram 通知 (未設定 Token)")

    print("\n測試結束！請檢查手機上的 Line 或 Telegram 通知，並嘗試點擊其中的「詳情」網址。")

if __name__ == "__main__":
    test_notification()
