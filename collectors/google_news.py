"""
Google News RSS 搜集器
透過 Google News RSS Feed 搜集麥當勞相關新聞
"""
import feedparser
from urllib.parse import quote
from datetime import datetime

from collectors.base import BaseCollector
import config


class GoogleNewsCollector(BaseCollector):
    """Google News RSS 搜集器"""

    BASE_URL = "https://news.google.com/rss/search"

    def __init__(self):
        super().__init__("Google News")

    def collect(self, keywords: list[str] = None) -> list[dict]:
        if keywords is None:
            keywords = config.SEARCH_KEYWORDS

        articles = []
        for keyword in keywords:
            try:
                items = self._fetch_feed(keyword)
                articles.extend(items)
            except Exception as e:
                print(f"[GoogleNews] 搜集關鍵字 '{keyword}' 時發生錯誤: {e}")

        # 依 URL 去重
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)

        print(f"[GoogleNews] 共搜集到 {len(unique_articles)} 篇不重複新聞")
        return unique_articles

    def _fetch_feed(self, keyword: str) -> list[dict]:
        """解析單一關鍵字的 RSS Feed，僅針對昨日進行精確搜尋"""
        from datetime import timedelta
        
        # 計算昨天與今天的日期字串 (YYYY-MM-DD)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        before_yesterday = today - timedelta(days=2)
        
        # 建立 Google News 搜尋算子
        # after:2026-03-24 before:2026-03-26 代表搜尋 3/25 整天
        date_filter = f" after:{before_yesterday.strftime('%Y-%m-%d')} before:{today.strftime('%Y-%m-%d')}"
        keyword_with_date = f"{keyword}{date_filter}"
        
        encoded_keyword = quote(keyword_with_date)
        url = (
            f"{self.BASE_URL}?q={encoded_keyword}"
            f"&hl={config.GOOGLE_NEWS_LANG}"
            f"&gl={config.GOOGLE_NEWS_REGION}"
            f"&ceid={config.GOOGLE_NEWS_REGION}:{config.GOOGLE_NEWS_LANG}"
        )


        feed = feedparser.parse(url)
        articles = []

        # 用於嚴格過濾發布日期的字串
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        for entry in feed.entries:
            published_at = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_at = datetime(
                        *entry.published_parsed[:6]
                    ).isoformat()
                except Exception:
                    published_at = entry.get("published", "")

            # 🛑 嚴格過濾：若發布日期早於昨天，則跳過，確保只搜集到昨天的文章
            if published_at and published_at[:10] < yesterday_str:
                continue

            # 取得來源名稱
            source_name = "Unknown"
            if hasattr(entry, 'source') and isinstance(entry.source, dict):
                source_name = entry.source.get('title', 'Unknown')
            elif hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                source_name = entry.source.title

            title = entry.get("title", "")
            # 移除常見的 " - 媒體名稱" 結尾
            if " - " in title:
                title = " - ".join(title.split(" - ")[:-1])

            article = {
                "title": title,
                "content": entry.get("summary", ""),
                "source": "Google News",  # 統一來源名稱，方便篩選
                "url": entry.get("link", ""),
                "published_at": published_at,
                "raw_data": {
                    "feed_title": feed.feed.get("title", ""),
                    "entry_id": entry.get("id", ""),
                    "original_source": source_name,
                },
            }
            articles.append(article)

        return articles
