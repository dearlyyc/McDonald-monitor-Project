"""
Tavily Search 搜集器
透過 Tavily API 搜尋品牌相關的最新資訊
"""
import requests
from datetime import datetime

from collectors.base import BaseCollector
import config


class TavilySearchCollector(BaseCollector):
    """Tavily Search 搜集器"""

    API_URL = "https://api.tavily.com/search"

    def __init__(self):
        super().__init__("Tavily Search")
        self.api_key = config.TAVILY_API_KEY

    def collect(self, keywords: list[str] | None = None) -> list[dict]:
        """
        透過 Tavily API 搜尋資訊。

        Args:
            keywords: 搜尋關鍵字
        Returns:
            文章列表
        """
        if not self.api_key:
            print("[Tavily] 未設定 TAVILY_API_KEY，跳過搜尋")
            return []

        articles = []
        # 使用傳入的所有關鍵字進行搜尋
        if not keywords:
            keywords = ["麥當勞", "麥當勞 活動", "麥當勞 優惠"]
        
        # 計算昨日日期
        from datetime import timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        for kw in keywords[:3]: 
            queries = [
                f"{kw} {yesterday}", # 使用具體日期精確搜尋
                f"麥當勞 news {yesterday}" # 加入 news 加強新聞屬性
            ]

            for query in queries:
                try:
                    items = self._search_tavily(query)
                    articles.extend(items)
                except Exception as e:
                    print(f"[Tavily] 搜尋 '{query}' 時發生錯誤: {e}")

        # 依 URL 去重
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)

        print(f"[Tavily] 共搜集到 {len(unique_articles)} 篇不重複文章")
        return unique_articles

    def _search_tavily(self, query: str) -> list[dict]:
        """呼叫 Tavily API"""
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "time_range": "m", # 限制在最近一個月內
            "include_images": False,
            "include_answer": False,
            "include_raw_content": False,
            "max_results": 5
        }

        try:
            resp = requests.post(self.API_URL, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"[Tavily] 請求失敗: {e}")
            return []

        articles = []
        results = data.get("results", [])

        for item in results:
            try:
                title = item.get("title", "")
                content = item.get("content", "")
                url = item.get("url", "")
                published_at = item.get("published_date", self._now_iso())
                
                # 🛑 嚴格過濾：僅保留昨天的文章
                from datetime import timedelta
                yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                if published_at and published_at[:10] < yesterday_str:
                    continue

                if not title or not url:
                    continue

                article = {
                    "title": title[:100],
                    "content": content[:2000],
                    "source": "Tavily Search",
                    "url": url,
                    "published_at": published_at,
                    "raw_data": {
                        "score": item.get("score"),
                        "query": query,
                    },
                }
                articles.append(article)
            except Exception as e:
                print(f"[Tavily] 解析結果時發生錯誤: {e}")
                continue

        return articles
