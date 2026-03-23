"""
DuckDuckGo Search 搜集器
透過 duckduckgo-search 套件搜尋品牌相關資訊
"""
from duckduckgo_search import DDGS
from datetime import datetime

from collectors.base import BaseCollector
import config

class DDGSearchCollector(BaseCollector):
    """DuckDuckGo Search 搜集器"""

    def __init__(self):
        super().__init__("DuckDuckGo Search")

    def collect(self, keywords: list[str] = None) -> list[dict]:
        """
        透過 DuckDuckGo 搜尋資訊。
        """
        articles = []
        if not keywords:
            keywords = ["麥當勞", "麥當勞 活動", "麥當勞 優惠"]
        
        # 針對關鍵字組合進行搜尋
        queries = []
        for kw in keywords[:3]:
            queries.extend([f"{kw} 2026", f"{kw} 最新新聞"])

        ddgs = DDGS()
        for query in queries:
            try:
                # 使用 text 搜尋，並限制時間在「最近一週」 (w) 內
                results = ddgs.text(query, max_results=5, timelimit='w')
                for item in results:
                    title = item.get("title", "")
                    content = item.get("body", "")
                    url = item.get("href", "")
                    
                    if not title or not url:
                        continue

                    article = {
                        "title": title[:100],
                        "content": content[:2000],
                        "source": "DuckDuckGo Search",
                        "url": url,
                        "published_at": self._now_iso(),
                        "raw_data": {
                            "query": query,
                        },
                    }
                    articles.append(article)
            except Exception as e:
                print(f"[DuckDuckGo] 搜尋 '{query}' 時發生錯誤: {e}")

        # 依 URL 去重
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)

        print(f"[DuckDuckGo] 共搜集到 {len(unique_articles)} 篇不重複文章")
        return unique_articles
