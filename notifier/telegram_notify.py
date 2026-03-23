"""
Telegram Bot 通知模組
透過 Telegram Bot API 發送輿情監控通知
"""
import requests

import config


class TelegramNotifier:
    """Telegram Bot 通知發送器"""

    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID

    @property
    def is_configured(self) -> bool:
        """檢查是否已設定 Token 和 Chat ID"""
        return bool(self.token and self.chat_id)

    def send(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        發送 Telegram 訊息。

        Args:
            message: 通知訊息
            parse_mode: 訊息格式 (Markdown / HTML)

        Returns:
            是否發送成功
        """
        if not self.is_configured:
            print("[Telegram] 未設定 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID，跳過通知")
            return False

        url = self.API_URL.format(token=self.token)
        payload = {
            "chat_id": self.chat_id,
            "text": message[:4096],
            "parse_mode": parse_mode,
        }

        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
            if data.get("ok"):
                print("[Telegram] 通知發送成功")
                return True
            else:
                print(f"[Telegram] 通知發送失敗: {data.get('description')}")
                return False
        except requests.RequestException as e:
            print(f"[Telegram] 通知發送錯誤: {e}")
            return False

    def send_summary(self, stats: dict, negative_articles: list[dict] = None,
                     positive_articles: list[dict] = None, source_stats: dict = None,
                     trend_stats: dict = None, ai_summary: str = None,
                     promo_articles: list[dict] = None):
        """發送精簡版監控摘要通知"""
        msg_lines = ["🍔 *麥當勞輿情摘要*"]

        if ai_summary:
            msg_lines.append(f"💡 AI 總結: {ai_summary}")

        msg_lines.append(
            f"📊 總數: *{stats.get('total', 0)}* | "
            f"正: *{stats.get('positive', 0)}* | "
            f"負: *{stats.get('negative', 0)}* | "
            f"中: *{stats.get('neutral', 0)}*"
        )

        if trend_stats and (trend_stats.get('diff_negative', 0) != 0 or trend_stats.get('diff_positive', 0) != 0):
            dn = trend_stats.get('diff_negative', 0)
            dp = trend_stats.get('diff_positive', 0)
            msg_lines.append(f"📈 趨勢: 負 {'+' if dn >= 0 else ''}{dn} | 正 {'+' if dp >= 0 else ''}{dp}")

        if promo_articles:
            msg_lines.append("\n🎁 *最新活動：*")
            for i, article in enumerate(promo_articles[:3], 1):
                title = article.get("title", "無標題")[:30]
                url = article.get("url", "")
                if url:
                    msg_lines.append(f"• [{title}]({url})")
                else:
                    msg_lines.append(f"• {title}")

        if negative_articles:
            msg_lines.append("\n⚠️ *負面重點：*")
            for i, article in enumerate(negative_articles[:3], 1):
                title = article.get("title", "無標題")[:30]
                url = article.get("url", "")
                if url:
                    msg_lines.append(f"{i}. [{title}]({url})")
                else:
                    msg_lines.append(f"{i}. {title}")

        msg_lines.append(f"\n🔗 [詳細報告]({config.APP_URL})")
        message = "\n".join(msg_lines)
        self.send(message)
