"""
Line Notify 通知模組
透過 Line Notify API 發送輿情監控通知
"""
import requests

import config


class LineNotifier:
    """LINE Messaging API 通知發送器 (取代已停用的 Notify)"""

    PUSH_URL = "https://api.line.me/v2/bot/message/push"

    def __init__(self):
        self.token = config.LINE_CHANNEL_ACCESS_TOKEN
        self.user_id = config.LINE_USER_ID

    @property
    def is_configured(self) -> bool:
        """檢查是否已設定傳訊所需的 Token 與 ID"""
        return bool(self.token) and bool(self.user_id)

    def send(self, message: str) -> bool:
        """
        發送 LINE Messaging API 推播通知。

        Args:
            message: 通知訊息
        """
        if not self.is_configured:
            print("[LINE] 未完整設定 LINE_CHANNEL_ACCESS_TOKEN 或 USER_ID，跳過")
            return False

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        payload = {
            "to": self.user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message[:5000] # Messaging API 上限更高
                }
            ]
        }

        try:
            resp = requests.post(
                self.PUSH_URL,
                headers=headers,
                json=payload,
                timeout=10,
            )
            if resp.status_code == 200:
                print("[LINE] 通知發送成功")
                return True
            else:
                print(f"[LINE] 通知發送失敗: {resp.status_code} {resp.text}")
                return False
        except requests.RequestException as e:
            print(f"[LINE] 通知發送錯誤: {e}")
            return False

    def send_summary(self, stats: dict, negative_articles: list[dict] = None,
                     positive_articles: list[dict] = None, source_stats: dict = None,
                     trend_stats: dict = None, ai_summary: str = None,
                     promo_articles: list[dict] = None):
        """發送精簡版監控摘要通知"""
        msg_lines = ["\n🍔 麥當勞輿情摘要"]

        if ai_summary:
            msg_lines.append(f"\n💡 AI 總結: {ai_summary}")

        msg_lines.append(
            f"\n📊 總數: {stats.get('total', 0)} | "
            f"正: {stats.get('positive', 0)} | "
            f"負: {stats.get('negative', 0)} | "
            f"中: {stats.get('neutral', 0)}"
        )

        if trend_stats and (trend_stats.get('diff_negative', 0) != 0 or trend_stats.get('diff_positive', 0) != 0):
            dn = trend_stats.get('diff_negative', 0)
            dp = trend_stats.get('diff_positive', 0)
            msg_lines.append(f"📈 趨勢: 負 {'+' if dn >= 0 else ''}{dn} | 正 {'+' if dp >= 0 else ''}{dp}")

        if promo_articles:
            msg_lines.append("\n🎁 最新活動：")
            for i, article in enumerate(promo_articles[:3], 1):
                title = article.get("title", "無標題")[:25]
                msg_lines.append(f"• {title}")

        if negative_articles:
            msg_lines.append("\n⚠️ 負面重點：")
            for i, article in enumerate(negative_articles[:3], 1):
                title = article.get("title", "無標題")[:25]
                msg_lines.append(f"{i}. {title}")

        msg_lines.append(f"\n🔗 詳情: {config.APP_URL}")
        message = "\n".join(msg_lines)
        self.send(message)
