"""
搜集器基類 - 定義統一的搜集介面
"""
from abc import ABC, abstractmethod
from datetime import datetime


class BaseCollector(ABC):
    """所有搜集器的抽象基類"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def collect(self, keywords: list[str]) -> list[dict]:
        """
        搜集資料。

        Args:
            keywords: 搜尋關鍵字列表

        Returns:
            統一格式的文章列表，每篇文章為 dict：
            {
                "title": str,        # 標題
                "content": str,      # 內容/摘要
                "source": str,       # 來源名稱
                "url": str,          # 原文連結
                "published_at": str, # 發布時間 (ISO format)
                "raw_data": dict,    # 原始資料
            }
        """
        pass

    def _now_iso(self) -> str:
        """取得目前時間的 ISO 格式字串"""
        return datetime.now().isoformat()
