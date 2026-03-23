"""
Line Notify 通知模組
透過 Line Notify API 發送輿情監控通知
"""
import requests
from datetime import datetime

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
                print(f"[LINE] API 回傳 200 (OK)，訊息已成功推播")
                return True
            else:
                print(f"[LINE] API 錯誤! 狀態碼: {resp.status_code}")
                print(f"       訊息內容: {resp.text}")
                return False
        except requests.RequestException as e:
            print(f"[LINE] 通知發送錯誤: {e}")
            return False

    def send_summary(self, stats: dict, negative_articles: list = None,
                     positive_articles: list = None, source_stats: dict = None,
                     trend_stats: dict = None, ai_summary: str = None,
                     promo_articles: list = None):
        """發送完整文字版監控彙總報告"""
        msg_lines = ["🍔 【麥當勞品牌輿情彙總】"]
        msg_lines.append(f"📅 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        if ai_summary:
            msg_lines.append(f"\n💡 【AI 深度洞察】\n{ai_summary}")

        msg_lines.append(
            f"\n📊 【情感統計】\n總數: {stats.get('total', 0)} | "
            f"🟢 正面: {stats.get('positive', 0)} | "
            f"🔴 負面: {stats.get('negative', 0)} | "
            f"⚪ 中立: {stats.get('neutral', 0)}"
        )

        if trend_stats:
            dn = trend_stats.get('diff_negative', 0)
            dp = trend_stats.get('diff_positive', 0)
            if dn != 0 or dp != 0:
                msg_lines.append(f"📈 趨勢對比: 負面 {'+' if dn >= 0 else ''}{dn} | 正面 {'+' if dp >= 0 else ''}{dp}")

        if promo_articles:
            msg_lines.append("\n🎁 【最新活動與推廣】")
            for i, article in enumerate(promo_articles[:5], 1):
                title = article.get("title", "無標題")
                msg_lines.append(f"{i}. {title}")

        if negative_articles:
            msg_lines.append("\n⚠️ 【負面輿情追蹤】")
            for i, article in enumerate(negative_articles[:5], 1):
                title = article.get("title", "無標題")
                msg_lines.append(f"{i}. {title}")

        msg_lines.append("\n✅ 報告已完成分析並發送完畢。")
        message = "\n".join(msg_lines)
        self.send(message)
