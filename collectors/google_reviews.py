"""
Google Maps 評論搜集器
透過 Google Maps 搜尋結果間接取得麥當勞評論資訊
若有 APIFY_TOKEN 則使用 Apify Actor 取得詳細評論
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from collectors.base import BaseCollector
import config


class GoogleReviewsCollector(BaseCollector):
    """Google Maps 評論搜集器"""

    def __init__(self):
        super().__init__("Google Reviews")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        })

    def collect(self, keywords: list[str] = None) -> list[dict]:
        if keywords is None:
            keywords = config.GOOGLE_PLACES_KEYWORDS

        # 優先使用 Apify
        if config.APIFY_TOKEN:
            return self._collect_via_apify(keywords)
        else:
            print("[GoogleReviews] 未設定 APIFY_TOKEN，改用 DuckDuckGo 搜尋 Google 評論")
            return self._collect_via_ddg(keywords)

    def _collect_via_apify(self, keywords: list[str]) -> list[dict]:
        """透過 Apify 搜集 Google Maps 評論"""
        try:
            from apify_client import ApifyClient
        except ImportError:
            print("[GoogleReviews] 未安裝 apify-client，跳過 Apify 搜集")
            return self._collect_via_ddg(keywords)

        client = ApifyClient(config.APIFY_TOKEN)
        articles = []

        for keyword in keywords:
            try:
                search_term = f"{keyword} 台灣"
                print(f"[GoogleReviews] 正在透過 Apify 搜尋: {search_term}")

                run_input = {
                    "searchStringsArray": [search_term],
                    "maxReviews": 20,
                    "language": "zh-TW",
                }

                run = client.actor("apify/google-maps-scraper").call(
                    run_input=run_input
                )

                for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                    # 有些結果帶有 reviews 陣列
                    reviews = item.get("reviews", [])
                    place_title = item.get("title", keyword)

                    if reviews:
                        for review in reviews[:20]:
                            text = review.get("text", "")
                            if not text:
                                continue

                            stars = review.get("stars", 0)
                            article = {
                                "title": f"使用者 {author} 的評論 ({stars}星)",
                                "content": text[:2000],
                                "source": "Google Reviews",
                                "url": review.get("reviewUrl", item.get("url", "")),
                                "published_at": review.get("publishedAtDate", self._now_iso()),
                                "raw_data": {
                                    "stars": stars,
                                    "author": author,
                                },
                            }
                            articles.append(article)
                    else:
                        # 沒有 reviews 但有整體評分資訊
                        total_score = item.get("totalScore", 0)
                        reviews_count = item.get("reviewsCount", 0)
                        if total_score:
                            article = {
                                "title": f"Google 地圖總體評分: {total_score}/5",
                                "content": f"{place_title} 的 Google Maps 評分為 {total_score}/5，共有 {reviews_count} 則評論。",
                                "source": "Google Reviews",
                                "url": item.get("url", ""),
                                "published_at": self._now_iso(),
                                "raw_data": {
                                    "total_score": total_score,
                                    "reviews_count": reviews_count,
                                },
                            }
                            articles.append(article)
            except Exception as e:
                print(f"[GoogleReviews] Apify 搜集 '{keyword}' 時發生錯誤: {e}")

        # 去重
        seen = set()
        unique = []
        for a in articles:
            key = a["url"] or a["title"]
            if key not in seen:
                seen.add(key)
                unique.append(a)

        print(f"[GoogleReviews] 共搜集到 {len(unique)} 則評論")
        return unique

    def _collect_via_ddg(self, keywords: list[str]) -> list[dict]:
        """透過 DuckDuckGo 搜尋 Google 評論做為備援"""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            print("[GoogleReviews] 未安裝 duckduckgo-search，跳過搜集")
            return []

        articles = []
        with DDGS() as ddgs:
            for keyword in keywords:
                query = f"{keyword} 評論 評價 心得"
                try:
                    results = ddgs.text(query, max_results=8)
                    for item in results:
                        title = item.get("title", "")
                        content = item.get("body", "")
                        url = item.get("href", "")
                        if not title or not url:
                            continue

                        article = {
                            "title": title[:100],
                            "content": content[:2000],
                            "source": "Google Reviews",
                            "url": url,
                            "published_at": self._now_iso(),
                            "raw_data": {"query": query},
                        }
                        articles.append(article)
                except Exception as e:
                    print(f"[GoogleReviews] DDG 搜尋 '{keyword}' 時錯誤: {e}")

        seen = set()
        unique = []
        for a in articles:
            if a["url"] not in seen:
                seen.add(a["url"])
                unique.append(a)

        print(f"[GoogleReviews] 共搜集到 {len(unique)} 則評論 (DuckDuckGo fallback)")
        return unique
