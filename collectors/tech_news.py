"""
科技新聞搜集器 - 抓取 iThome, 數位時代, TechNews, 未來城市, INSIDE
"""
import feedparser
import requests
from datetime import datetime
from typing import List, Dict

from collectors.base import BaseCollector

class TechNewsCollector(BaseCollector):
    def __init__(self):
        super().__init__("TechNews")
        self.sources = [
            {"name": "iThome", "url": "https://www.ithome.com.tw/rss"},
            {"name": "數位時代", "url": "https://www.bnext.com.tw/feed/"},
            {"name": "TechNews 科技新報", "url": "https://technews.tw/feed/"},
            {"name": "未來城市", "url": "https://www.cw.com.tw/rss/channel/129"},
            {"name": "INSIDE 硬塞網路", "url": "https://www.inside.com.tw/feed/"}
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def collect(self, keywords: List[str] | None = None) -> List[Dict]:
        """
        搜集科技新聞。
        """
        all_articles = []
        for source in self.sources:
            try:
                # 使用 requests 獲取內容以帶入 Headers，避免被擋
                resp = requests.get(source["url"], headers=self.headers, timeout=15)
                if resp.status_code != 200:
                    print(f"Failed to fetch {source['name']}: HTTP {resp.status_code}")
                    continue
                
                feed = feedparser.parse(resp.content)
                for entry in feed.entries[:20]: # 每個來源取最新的 20 則
                    published = ""
                    if hasattr(entry, "published"):
                        published = entry.published
                    elif hasattr(entry, "updated"):
                        published = entry.updated
                    
                    # 轉換時間格式 (簡易處理)
                    try:
                        # feedparser 通常會處理成 struct_time，轉換為 ISO 字串
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            published = datetime(*entry.published_parsed[:6]).isoformat()
                    except:
                        pass

                    all_articles.append({
                        "title": entry.title,
                        "content": entry.get("summary", entry.get("description", "")),
                        "source": source["name"],
                        "url": entry.link,
                        "published_at": published,
                        "raw_data": {"author": entry.get("author", "Unknown")}
                    })
            except Exception as e:
                print(f"Error collecting from {source['name']}: {e}")
        
        return all_articles

if __name__ == "__main__":
    collector = TechNewsCollector()
    news = collector.collect()
    print(f"Collected {len(news)} news articles.")
    for n in news[:3]:
        print(f"- {n['title']} ({n['source']})")
