"""
麥當勞品牌輿情監控系統 - 資料庫模組
使用 SQLite 儲存搜集到的文章與分析結果
"""
import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

from typing import Optional, Union, List, Dict
import config


def get_connection():
    """取得資料庫連線"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化資料庫表格"""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                summary TEXT,
                source TEXT NOT NULL,
                url TEXT UNIQUE,
                sentiment TEXT DEFAULT 'neutral',
                sentiment_score REAL DEFAULT 0.0,
                sentiment_reason TEXT,
                published_at TEXT,
                collected_at TEXT NOT NULL,
                analyzed_at TEXT,
                raw_data TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_articles_sentiment
                ON articles(sentiment);
            CREATE INDEX IF NOT EXISTS idx_articles_source
                ON articles(source);
            CREATE INDEX IF NOT EXISTS idx_articles_collected_at
                ON articles(collected_at);
            CREATE INDEX IF NOT EXISTS idx_articles_published_at
                ON articles(published_at);

            CREATE TABLE IF NOT EXISTS monitor_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at TEXT NOT NULL,
                total_collected INTEGER DEFAULT 0,
                total_analyzed INTEGER DEFAULT 0,
                positive_count INTEGER DEFAULT 0,
                negative_count INTEGER DEFAULT 0,
                neutral_count INTEGER DEFAULT 0,
                notification_sent INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                error_message TEXT
            );
        """)


def insert_article(article: dict) -> int | None:
    """
    新增一篇文章到資料庫。
    若 URL 已存在則忽略。
    回傳新文章的 ID，若已存在回傳 None。
    """
    with get_db() as conn:
        try:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO articles
                    (title, content, source, url, published_at, collected_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                article.get("title", ""),
                article.get("content", ""),
                article.get("source", ""),
                article.get("url", ""),
                article.get("published_at", ""),
                datetime.now().isoformat(),
                json.dumps(article.get("raw_data", {}), ensure_ascii=False),
            ))
            if cursor.rowcount > 0:
                return cursor.lastrowid
            return None
        except sqlite3.IntegrityError:
            return None


def update_sentiment(article_id: int, sentiment: str, score: float,
                     reason: str, summary: str):
    """更新文章的情感分析結果"""
    with get_db() as conn:
        conn.execute("""
            UPDATE articles
            SET sentiment = ?, sentiment_score = ?, sentiment_reason = ?,
                summary = ?, analyzed_at = ?
            WHERE id = ?
        """, (sentiment, score, reason, summary,
              datetime.now().isoformat(), article_id))


def get_unanalyzed_articles(limit: int = 200) -> list[dict]:
    """取得尚未分析的文章列表"""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, title, content, source, url, published_at
            FROM articles
            WHERE analyzed_at IS NULL
            ORDER BY collected_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]


def _get_date_range(days: int | str = 7) -> tuple[str, str]:
    """統一處理日期範圍邏輯，回傳 (since_date, time_field)"""
    if days == "yesterday":
        since = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        return since, "analyzed_at"
    elif str(days) == "1":
        since = datetime.now().strftime('%Y-%m-%d')
        return since, "analyzed_at"
    else:
        try:
            d_count = int(days)
        except:
            d_count = 7
        since = (datetime.now() - timedelta(days=d_count)).isoformat()
        return since, "collected_at"

def get_articles(sentiment: Optional[str] = None, source: Optional[str] = None,
                 days: Union[int, str] = 7, page: int = 1,
                 per_page: int = 20, query: Optional[str] = None) -> dict:
    """
    查詢文章列表，支援篩選與分頁。
    回傳 { articles, total, page, per_page, pages }
    """
    conditions = []
    params = []

    since_date, time_field = _get_date_range(days)
    
    if days == "yesterday":
        today_date = datetime.now().strftime('%Y-%m-%d')
        conditions.append(f"{time_field} >= ?")
        conditions.append(f"{time_field} < ?")
        params.extend([since_date, today_date])
    else:
        conditions.append(f"{time_field} >= ?")
        params.append(since_date)


    if sentiment and sentiment != "all":
        conditions.append("sentiment = ?")
        params.append(sentiment)
    if source and source != "all":
        conditions.append("source = ?")
        params.append(source)
    if query and query.strip():
        conditions.append("(title LIKE ? OR content LIKE ?)")
        search_val = f"%{query.strip()}%"
        params.append(search_val)
        params.append(search_val)

    where_clause = " AND ".join(conditions)

    with get_db() as conn:
        # 總數
        total = conn.execute(
            f"SELECT COUNT(*) FROM articles WHERE {where_clause}", params
        ).fetchone()[0]

        # 分頁查詢
        offset = (page - 1) * per_page
        rows = conn.execute(f"""
            SELECT * FROM articles
            WHERE {where_clause}
            ORDER BY collected_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset]).fetchall()

        pages = max(1, (total + per_page - 1) // per_page)

        return {
            "articles": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }


def get_sentiment_stats(days: int | str = 7) -> dict:
    """取得情感分析統計"""
    since, time_field = _get_date_range(days)
    
    with get_db() as conn:
        rows = conn.execute(f"""
            SELECT sentiment, COUNT(*) as count
            FROM articles
            WHERE {time_field} >= ? AND analyzed_at IS NOT NULL
            GROUP BY sentiment
        """, (since,)).fetchall()

        stats = {"positive": 0, "negative": 0, "neutral": 0}
        for row in rows:
            if row["sentiment"] in stats:
                stats[row["sentiment"]] = row["count"]

        total = sum(stats.values())
        stats["total"] = total
        return stats


def get_source_stats(days: int | str = 7) -> list[dict]:
    """取得平台來源統計"""
    since, time_field = _get_date_range(days)
    
    with get_db() as conn:
        rows = conn.execute(f"""
            SELECT source, COUNT(*) as count
            FROM articles
            WHERE {time_field} >= ?
            GROUP BY source
        """, (since,)).fetchall()
        return [{"source": row["source"], "count": row["count"]} for row in rows]


def get_trend_stats() -> dict:
    """比較今日與昨日的情感聲量變化"""
    today_since = (datetime.now() - timedelta(days=1)).isoformat()
    yesterday_since = (datetime.now() - timedelta(days=2)).isoformat()
    with get_db() as conn:
        today_rows = conn.execute("""
            SELECT sentiment, COUNT(*) as count
            FROM articles
            WHERE collected_at >= ? AND analyzed_at IS NOT NULL
            GROUP BY sentiment
        """, (today_since,)).fetchall()
        yesterday_rows = conn.execute("""
            SELECT sentiment, COUNT(*) as count
            FROM articles
            WHERE collected_at >= ? AND collected_at < ? AND analyzed_at IS NOT NULL
            GROUP BY sentiment
        """, (yesterday_since, today_since)).fetchall()
        
        t_stats = {row["sentiment"]: row["count"] for row in today_rows}
        y_stats = {row["sentiment"]: row["count"] for row in yesterday_rows}
        return {
            "today_total": sum(t_stats.values()),
            "diff_total": sum(t_stats.values()) - sum(y_stats.values()),
            "diff_negative": t_stats.get('negative', 0) - y_stats.get('negative', 0),
            "diff_positive": t_stats.get('positive', 0) - y_stats.get('positive', 0)
        }



def get_daily_stats(days: int = 30) -> list[dict]:
    """取得每日情感統計（用於圖表）"""
    since = (datetime.now() - timedelta(days=days)).isoformat()
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                DATE(collected_at) as date,
                sentiment,
                COUNT(*) as count
            FROM articles
            WHERE collected_at >= ? AND analyzed_at IS NOT NULL
            GROUP BY DATE(collected_at), sentiment
            ORDER BY date
        """, (since,)).fetchall()

        daily = {}
        for row in rows:
            date_str = row["date"]
            if date_str not in daily:
                daily[date_str] = {"date": date_str, "positive": 0,
                                   "negative": 0, "neutral": 0}
            daily[date_str][row["sentiment"]] = row["count"]

        return list(daily.values())


def insert_monitor_log(log: dict):
    """新增監控執行記錄"""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO monitor_logs
                (run_at, total_collected, total_analyzed,
                 positive_count, negative_count, neutral_count,
                 notification_sent, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            log.get("total_collected", 0),
            log.get("total_analyzed", 0),
            log.get("positive_count", 0),
            log.get("negative_count", 0),
            log.get("neutral_count", 0),
            log.get("notification_sent", 0),
            log.get("status", "success"),
            log.get("error_message", ""),
        ))


def get_recent_logs(limit: int = 10) -> list[dict]:
    """取得最近的監控執行記錄"""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM monitor_logs
            ORDER BY run_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]


def get_sentiment_summaries() -> dict:
    """取得正、負、中立各一則代表性的最新摘要 (僅限今日)"""
    today = datetime.now().strftime('%Y-%m-%d')
    with get_db() as conn:
        res = {}
        for sentiment in ['positive', 'negative', 'neutral']:
            # 僅搜尋今日分析完成且具有摘要的文章
            row = conn.execute("""
                SELECT summary, title 
                FROM articles 
                WHERE sentiment = ? 
                AND summary IS NOT NULL 
                AND summary != ''
                AND analyzed_at LIKE ?
                ORDER BY analyzed_at DESC LIMIT 1
            """, (sentiment, f"{today}%")).fetchone()
            
            if row:
                res[sentiment] = {
                    "summary": row["summary"],
                    "title": row["title"]
                }
            else:
                res[sentiment] = {
                    "summary": "今日尚未產出此類別的分析摘要數據。",
                    "title": "今日無摘要"
                }
        return res

