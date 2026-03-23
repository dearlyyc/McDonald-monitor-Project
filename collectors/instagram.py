"""
Instagram 公開貼文搜集器
透過 Apify apify/instagram-scraper 搜集麥當勞公開貼文
若未設定 APIFY_TOKEN，則透過 DuckDuckGo 補充搜尋 Instagram 相關內容
"""
import requests
from datetime import datetime

from collectors.base import BaseCollector
import config


class InstagramCollector(BaseCollector):
    """Instagram 公開搜集器"""

    def __init__(self):
        super().__init__("Instagram")

    def collect(self, keywords: list[str] = None) -> list[dict]:
        if keywords is None:
            keywords = config.SEARCH_KEYWORDS

        # 優先使用 Apify
        if config.APIFY_TOKEN:
            return self._collect_via_apify()
        else:
            print("[Instagram] 未設定 APIFY_TOKEN，改用 DuckDuckGo 搜尋 IG 貼文")
            return self._collect_via_ddg(keywords)

    def _collect_via_apify(self) -> list[dict]:
        """透過 Apify 搜集 Instagram 貼文"""
        try:
            from apify_client import ApifyClient
        except ImportError:
            print("[Instagram] 未安裝 apify-client，跳過 Apify 搜集")
            return []

        client = ApifyClient(config.APIFY_TOKEN)
        articles = []

        # 準備搜集目標
        targets = []
        for account in config.INSTAGRAM_ACCOUNTS:
            targets.append(f"https://www.instagram.com/{account}/")

        hashtags = ["麥當勞", "mcdonalds", "mcdonaldstw"]
        for tag in hashtags:
            targets.append(f"https://www.instagram.com/explore/tags/{tag}/")

        try:
            print(f"[Instagram] 正在透過 Apify 搜集 {len(targets)} 個目標...")

            run_input = {
                "directUrls": targets,
                "resultsLimit": 15,
            }

            run = client.actor("apify/instagram-scraper").call(
                run_input=run_input
            )

            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                caption = item.get("caption", "")
                if not caption:
                    continue

                url = item.get("url", "")
                owner = item.get("ownerUsername", "unknown")

                article = {
                    "title": caption[:60] + ("..." if len(caption) > 60 else ""),
                    "content": caption[:2000],
                    "source": "Instagram",
                    "url": url,
                    "published_at": item.get("timestamp", self._now_iso()),
                    "raw_data": {
                        "likes": item.get("likesCount", 0),
                        "comments": item.get("commentsCount", 0),
                        "owner": owner,
                    },
                }
                articles.append(article)
        except Exception as e:
            print(f"[Instagram] Apify 搜集時發生錯誤: {e}")

        # 去重
        seen = set()
        unique = []
        for a in articles:
            if a["url"] not in seen:
                seen.add(a["url"])
                unique.append(a)

        print(f"[Instagram] 共搜集到 {len(unique)} 篇貼文")
        return unique

    def _collect_via_ddg(self, keywords: list[str]) -> list[dict]:
        """透過 DuckDuckGo 搜尋 Instagram 相關內容做為備援"""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            print("[Instagram] 未安裝 duckduckgo-search，跳過搜集")
            return []

        articles = []
        with DDGS() as ddgs:
            for keyword in keywords:
                query = f"site:instagram.com {keyword}"
                try:
                    results = ddgs.text(query, max_results=5)
                    for item in results:
                        title = item.get("title", "")
                        content = item.get("body", "")
                        url = item.get("href", "")
                        if not title or not url:
                            continue

                        article = {
                            "title": title[:100],
                            "content": content[:2000],
                            "source": "Instagram",
                            "url": url,
                            "published_at": self._now_iso(),
                            "raw_data": {"query": query},
                        }
                        articles.append(article)
                except Exception as e:
                    print(f"[Instagram] DDG 搜尋 '{keyword}' 時發生錯誤: {e}")

        seen = set()
        unique = []
        for a in articles:
            if a["url"] not in seen:
                seen.add(a["url"])
                unique.append(a)

        print(f"[Instagram] 共搜集到 {len(unique)} 篇貼文 (DuckDuckGo fallback)")
        return unique
