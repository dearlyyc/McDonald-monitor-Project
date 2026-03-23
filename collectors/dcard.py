"""
Dcard 論壇搜集器
透過 Dcard 公開搜尋 API 搜集麥當勞相關貼文
"""
import requests
from datetime import datetime

from collectors.base import BaseCollector
import config


class DcardCollector(BaseCollector):
    """Dcard 論壇搜集器"""

    SEARCH_API = "https://www.dcard.tw/service/api/v2/search/posts"

    def __init__(self):
        super().__init__("Dcard")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.dcard.tw/",
        })

    def collect(self, keywords: list[str] = None) -> list[dict]:
        if keywords is None:
            keywords = config.SEARCH_KEYWORDS

        articles = []
        for keyword in keywords:
            try:
                items = self._search_posts(keyword)
                if not items:
                    print(f"[Dcard] API 無結果，嘗試透過 DuckDuckGo 備援...")
                    items = self._search_via_ddg(keyword)
                articles.extend(items)
            except Exception as e:
                print(f"[Dcard] 搜集關鍵字 '{keyword}' 時發生錯誤: {e}")

        # 依 URL 去重
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)

        print(f"[Dcard] 共搜集到 {len(unique_articles)} 篇不重複貼文")
        return unique_articles

    def _search_posts(self, keyword: str) -> list[dict]:
        """透過 Dcard 搜尋 API 搜尋貼文"""
        articles = []
        params = {
            "query": keyword,
            "limit": 30,
        }

        try:
            resp = self.session.get(self.SEARCH_API, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"[Dcard] API 請求失敗: {e}")
            return []
        except ValueError:
            print("[Dcard] API 回傳非 JSON 格式")
            return []

        for post in data:
            post_id = post.get("id", "")
            forum_alias = post.get("forumAlias", "")
            title = post.get("title", "")
            excerpt = post.get("excerpt", "") or post.get("content", "")

            published_at = post.get("createdAt", "")
            if published_at:
                try:
                    # Dcard 的 ISO 時間
                    published_at = published_at[:19]
                except Exception:
                    published_at = self._now_iso()

            article = {
                "title": title,
                "content": excerpt[:2000],
                "source": "Dcard",
                "url": f"https://www.dcard.tw/f/{forum_alias}/p/{post_id}",
                "published_at": published_at or self._now_iso(),
                "raw_data": {
                    "forum": forum_alias,
                    "like_count": post.get("likeCount", 0),
                    "comment_count": post.get("commentCount", 0),
                },
            }
            articles.append(article)

        return articles

    def _search_via_ddg(self, keyword: str) -> list[dict]:
        """透過 DuckDuckGo 備援搜尋 Dcard 貼文"""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return []

        articles = []
        with DDGS() as ddgs:
            query = f"site:dcard.tw {keyword}"
            try:
                results = ddgs.text(query, max_results=10)
                for item in results:
                    article = {
                        "title": item.get("title", ""),
                        "content": item.get("body", ""),
                        "source": "Dcard",
                        "url": item.get("href", ""),
                        "published_at": self._now_iso(),
                        "raw_data": {"search_via": "ddg"},
                    }
                    articles.append(article)
            except Exception:
                pass
        return articles
