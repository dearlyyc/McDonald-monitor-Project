"""
PTT 看板搜集器
爬取 PTT 網頁版搜集麥當勞相關貼文
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from collectors.base import BaseCollector
import config


class PTTCollector(BaseCollector):
    """PTT 看板搜集器"""

    BASE_URL = "https://www.ptt.cc"
    SEARCH_URL = "https://www.ptt.cc/bbs/{board}/search"

    def __init__(self):
        super().__init__("PTT")
        self.session = requests.Session()
        # PTT 需要 over18 cookie，設定時加入 domain
        self.session.cookies.set("over18", "1", domain="www.ptt.cc")
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/132.0.0.0 Safari/537.36"
            )
        })

    def collect(self, keywords: list[str] = None) -> list[dict]:
        """
        從 PTT 看板搜集貼文。

        Args:
            keywords: 搜尋關鍵字列表
        Returns:
            文章列表
        """
        if keywords is None:
            keywords = config.SEARCH_KEYWORDS

        articles = []
        for board in config.PTT_BOARDS:
            for keyword in keywords:
                try:
                    items = self._search_board(board, keyword)
                    articles.extend(items)
                except Exception as e:
                    print(f"[PTT] 搜集 {board} 板 '{keyword}' 時發生錯誤: {e}")

        # 依 URL 去重
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)

        print(f"[PTT] 共搜集到 {len(unique_articles)} 篇不重複貼文")
        return unique_articles

    def _search_board(self, board: str, keyword: str,
                      max_pages: int = 2) -> list[dict]:
        """搜尋特定看板的關鍵字"""
        articles = []
        url = f"{self.BASE_URL}/bbs/{board}/search?q={keyword}"

        for page in range(max_pages):
            try:
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"[PTT] 請求失敗: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            entries = soup.select("div.r-ent")

            if not entries:
                break

            for entry in entries:
                article = self._parse_entry(entry, board)
                if article:
                    articles.append(article)

            # 取得上一頁連結
            prev_link = soup.select_one("a.btn.wide:contains('上頁')")
            if prev_link and prev_link.get("href"):
                url = self.BASE_URL + prev_link["href"]
            else:
                break

        return articles

    def _parse_entry(self, entry, board: str) -> dict | None:
        """解析單一 PTT 文章列表項目"""
        title_el = entry.select_one("div.title a")
        if not title_el:
            return None

        title = title_el.get_text(strip=True)
        href = title_el.get("href", "")
        article_url = self.BASE_URL + href if href else ""

        # 取得日期
        date_el = entry.select_one("div.date")
        date_str = date_el.get_text(strip=True) if date_el else ""

        # 取得推文數
        nrec_el = entry.select_one("div.nrec span")
        popularity = nrec_el.get_text(strip=True) if nrec_el else "0"

        # 嘗試取得文章內容（限制長度以避免過多請求）
        content = ""
        if article_url:
            try:
                content = self._fetch_article_content(article_url)
            except Exception:
                content = ""

        # 將 PTT 日期格式轉為 ISO
        published_at = ""
        if date_str:
            try:
                now = datetime.now()
                month_day = date_str.strip().split("/")
                if len(month_day) == 2:
                    month = int(month_day[0])
                    day = int(month_day[1])
                    published_at = datetime(
                        now.year, month, day
                    ).isoformat()
            except (ValueError, IndexError):
                published_at = ""

        return {
            "title": title,
            "content": content[:2000],  # 限制內容長度
            "source": f"PTT ({board})",
            "url": article_url,
            "published_at": published_at,
            "raw_data": {
                "board": board,
                "popularity": popularity,
            },
        }

    def _fetch_article_content(self, url: str) -> str:
        """取得 PTT 文章的完整內容"""
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # 取得主文內容
            main_content = soup.select_one("#main-content")
            if not main_content:
                return ""

            # 移除 meta 資訊和推文
            for tag in main_content.select(
                "div.article-metaline, div.article-metaline-right, "
                "div.push, span.f2"
            ):
                tag.decompose()

            text = main_content.get_text(strip=True)
            return text
        except Exception:
            return ""
