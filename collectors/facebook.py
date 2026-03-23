"""
Facebook 公開貼文搜集器
透過 Apify apify/facebook-posts-scraper 搜集麥當勞粉絲頁貼文
若未設定 APIFY_TOKEN，則透過 DuckDuckGo 補充搜尋 Facebook 相關內容
"""
import requests
from datetime import datetime

from collectors.base import BaseCollector
import config


class FacebookCollector(BaseCollector):
    """Facebook 公開貼文搜集器"""

    def __init__(self):
        super().__init__("Facebook")

    def collect(self, keywords: list[str] = None) -> list[dict]:
        if keywords is None:
            keywords = config.SEARCH_KEYWORDS

        # 優先使用 Apify
        if config.APIFY_TOKEN:
            return self._collect_via_apify()
        else:
            print("[Facebook] 未設定 APIFY_TOKEN，改用 DuckDuckGo 搜尋 Facebook 貼文")
            return self._collect_via_ddg(keywords)

    def _collect_via_apify(self) -> list[dict]:
        """透過 Apify 搜集 Facebook 貼文"""
        try:
            from apify_client import ApifyClient
        except ImportError:
            print("[Facebook] 未安裝 apify-client，跳過 Apify 搜集")
            return []

        client = ApifyClient(config.APIFY_TOKEN)
        articles = []

        for page_name in config.FACEBOOK_PAGES:
            try:
                page_url = f"https://www.facebook.com/{page_name}"
                print(f"[Facebook] 正在透過 Apify 搜集粉絲頁: {page_name}")

                run_input = {
                    "startUrls": [{"url": page_url}],
                    "resultsLimit": 10,
                }

                run = client.actor("apify/facebook-posts-scraper").call(
                    run_input=run_input
                )

                for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                    text = item.get("text", "") or item.get("message", "")
                    if not text:
                        continue

                    url = item.get("url", item.get("postUrl", ""))

                    article = {
                        "title": text[:60] + ("..." if len(text) > 60 else ""),
                        "content": text[:2000],
                        "source": "Facebook",
                        "url": url,
                        "published_at": item.get("time", self._now_iso()),
                        "raw_data": {
                            "page_name": page_name,
                            "likes": item.get("likes", 0),
                            "comments": item.get("comments", 0),
                            "shares": item.get("shares", 0),
                        },
                    }
                    articles.append(article)
            except Exception as e:
                print(f"[Facebook] Apify 搜集 '{page_name}' 時發生錯誤: {e}")

        print(f"[Facebook] 共搜集到 {len(articles)} 篇貼文")
        return articles

    def _collect_via_ddg(self, keywords: list[str]) -> list[dict]:
        """透過 DuckDuckGo 搜尋 Facebook 相關內容做為備援"""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            print("[Facebook] 未安裝 duckduckgo-search，跳過搜集")
            return []

        articles = []
        with DDGS() as ddgs:
            for keyword in keywords:
                query = f"site:facebook.com {keyword}"
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
                            "source": "Facebook",
                            "url": url,
                            "published_at": self._now_iso(),
                            "raw_data": {"query": query},
                        }
                        articles.append(article)
                except Exception as e:
                    print(f"[Facebook] DDG 搜尋 '{keyword}' 時發生錯誤: {e}")

        # 去重
        seen = set()
        unique = []
        for a in articles:
            if a["url"] not in seen:
                seen.add(a["url"])
                unique.append(a)

        print(f"[Facebook] 共搜集到 {len(unique)} 篇貼文 (DuckDuckGo fallback)")
        return unique
