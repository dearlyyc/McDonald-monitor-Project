"""
Telegram Bot 通知模組
透過 Telegram Bot API 發送輿情監控通知
"""
import requests
from datetime import datetime
from typing import Optional, List, Dict

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

    def send_summary(self, stats: dict, negative_articles: Optional[list] = None,
                     positive_articles: Optional[list] = None, source_stats: Optional[dict] = None,
                     trend_stats: Optional[dict] = None, ai_summary: Optional[str] = None,
                     promo_articles: Optional[list] = None):
        """發送完整文字版監控彙總報告"""
        msg_lines = ["🍔 *【麥當勞品牌輿情彙總】*"]
        msg_lines.append(f"📅 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        if ai_summary:
            msg_lines.append(f"\n💡 *【AI 深度洞察】*\n{ai_summary}")

        msg_lines.append(
            f"\n📊 *【情感統計】*\n總數: *{stats.get('total', 0)}* | "
            f"🟢 正面: *{stats.get('positive', 0)}* | "
            f"🔴 負面: *{stats.get('negative', 0)}* | "
            f"⚪ 中立: *{stats.get('neutral', 0)}*"
        )

        if trend_stats:
            dn = trend_stats.get('diff_negative', 0)
            dp = trend_stats.get('diff_positive', 0)
            if dn != 0 or dp != 0:
                msg_lines.append(f"📈 趨勢對比: 負面 {'+' if dn >= 0 else ''}{dn} | 正面 {'+' if dp >= 0 else ''}{dp}")

        if promo_articles:
            msg_lines.append("\n🎁 *【最新活動與推廣】*")
            for i, article in enumerate(promo_articles[:5], 1):
                title = article.get("title", "無標題")[:50]
                url = article.get("url", "")
                if url:
                    msg_lines.append(f"{i}. [{title}]({url})")
                else:
                    msg_lines.append(f"{i}. {title}")

        if negative_articles:
            msg_lines.append("\n⚠️ *【負面輿情追蹤】*")
            for i, article in enumerate(negative_articles[:5], 1):
                title = article.get("title", "無標題")[:50]
                url = article.get("url", "")
                if url:
                    msg_lines.append(f"{i}. [{title}]({url})")
                else:
                    msg_lines.append(f"{i}. {title}")

        msg_lines.append(f"\n📑 [查看詳細輿情報告 (GitHub Pages)]({config.GITHUB_PAGES_URL})")
        msg_lines.append(f"\n🌐 [即時監控儀表板 (本機伺服器)]({config.APP_URL})")
        msg_lines.append("\n✅ 報告已分析完畢。")
        message = "\n".join(msg_lines)
        self.send(message, parse_mode="Markdown")
