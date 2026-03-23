"""
Line Notify 通知模組
透過 Line Notify API 發送輿情監控通知
"""
import requests

import config


class LineNotifier:
    """Line Notify 通知發送器"""

    NOTIFY_URL = "https://notify-api.line.me/api/notify"

    def __init__(self):
        self.token = config.LINE_NOTIFY_TOKEN

    @property
    def is_configured(self) -> bool:
        """檢查是否已設定 Token"""
        return bool(self.token)

    def send(self, message: str) -> bool:
        """
        發送 Line Notify 通知。

        Args:
            message: 通知訊息（上限 1000 字）

        Returns:
            是否發送成功
        """
        if not self.is_configured:
            print("[Line] 未設定 LINE_NOTIFY_TOKEN，跳過通知")
            return False

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            resp = requests.post(
                self.NOTIFY_URL,
                headers=headers,
                data={"message": message[:1000]},
                timeout=10,
            )
            if resp.status_code == 200:
                print("[Line] 通知發送成功")
                return True
            else:
                print(f"[Line] 通知發送失敗: {resp.status_code} {resp.text}")
                return False
        except requests.RequestException as e:
            print(f"[Line] 通知發送錯誤: {e}")
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
