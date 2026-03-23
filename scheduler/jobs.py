"""
排程任務模組
使用 APScheduler 定時執行搜集與分析任務
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

import config
import database
from collectors import (
    GoogleNewsCollector, PTTCollector, DcardCollector,
    FacebookCollector, InstagramCollector, GoogleReviewsCollector,
    TavilySearchCollector, DDGSearchCollector,
)
from analyzer import SentimentAnalyzer
from notifier import LineNotifier, TelegramNotifier


class MonitorScheduler:
    """監控排程管理器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        # 初始化所有搜集器
        self.collectors = [
            GoogleNewsCollector(),
            PTTCollector(),
            DcardCollector(),
            FacebookCollector(),
            InstagramCollector(),
            GoogleReviewsCollector(),
            TavilySearchCollector(),
            DDGSearchCollector(),
        ]
        self.analyzer = SentimentAnalyzer()
        self.line_notifier = LineNotifier()
        self.telegram_notifier = TelegramNotifier()
        self.is_running = False

    def start(self):
        """啟動排程器"""
        # Job 1: 每隔 X 小時執行一次背景搜集與分析 (不發通知)
        self.scheduler.add_job(
            self.run_monitor_cycle,
            "interval",
            hours=config.SCHEDULE_INTERVAL_HOURS,
            args=[False], # notify=False
            id="background_collect",
            name="背景輿情搜集 (每4小時)",
            next_run_time=datetime.now() # 啟動時立即執行一次
        )
        print(f"[Scheduler] 背景搜集已啟動，每 {config.SCHEDULE_INTERVAL_HOURS} 小時執行一次")

        # Job 2: 每天早上 10:00 發送彙報通知
        self.scheduler.add_job(
            self.send_daily_summary,
            "cron",
            hour=config.SCHEDULE_CRON_HOUR,
            minute=config.SCHEDULE_CRON_MINUTE,
            id="daily_report",
            name="每日彙報通知 (10:00)",
            misfire_grace_time=3600*24,
            coalesce=True
        )
        print(f"[Scheduler] 彙報通知已啟動，每天 {config.SCHEDULE_CRON_HOUR:02d}:00 發送摘要")

        self.scheduler.start()

    def stop(self):
        """停止排程器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("[Scheduler] 排程已停止")

    def run_monitor_cycle(self, notify=True):
        """
        執行一次完整的監控週期：
        搜集 → 儲存 → 分析 (→ 通知，選用)
        """
        if self.is_running:
            print("[Monitor] 週期已在運行中，跳過此次背景執行")
            return None
        
        self.is_running = True
        print(f"\n{'='*50}")
        print(f"[Monitor] 開始執行監控週期 - {datetime.now().isoformat()} (通知: {notify})")
        print(f"{'='*50}")

        log = {
            "total_collected": 0,
            "total_analyzed": 0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "notification_sent": 0,
            "status": "success",
            "error_message": "",
        }

        try:
            # Step 1 & 2: 搜集與儲存
            print("\n[Step 1 & 2] 搜集資料與儲存...")
            all_articles = []
            for collector in self.collectors:
                try:
                    items = collector.collect()
                    all_articles.extend(items)
                except Exception as e:
                    print(f"  ✗ {collector.name} 搜集失敗: {e}")

            new_count = 0
            for article in all_articles:
                if database.insert_article(article):
                    new_count += 1
            log["total_collected"] = new_count
            print(f"  ✓ 新增 {new_count} 篇文章")

            # Step 3: 情感分析
            print("\n[Step 3] 情感分析...")
            unanalyzed = database.get_unanalyzed_articles()
            if unanalyzed:
                results = self.analyzer.analyze_batch(unanalyzed)
                analyzed_count = 0
                for result in results:
                    if result.get("status") == "failed":
                        continue
                    database.update_sentiment(
                        article_id=result["article_id"],
                        sentiment=result["sentiment"],
                        score=result["score"],
                        reason=result["reason"],
                        summary=result["summary"],
                    )
                    log[f"{result['sentiment']}_count"] += 1
                    analyzed_count += 1
                log["total_analyzed"] = analyzed_count
                print(f"  ✓ 成功分析了 {analyzed_count} 篇文章")

            # Step 4: 指令要求發送通知時才發送
            if notify:
                self.send_daily_summary()

        except Exception as e:
            log["status"] = "error"
            log["error_message"] = str(e)[:500]
            print(f"\n[Monitor] 監控週期發生錯誤: {e}")
        finally:
            database.insert_monitor_log(log)
            self.is_running = False
            print(f"\n[Monitor] 監控週期完成 - 狀態: {log['status']}")
            print(f"{'='*50}\n")
        return log

    def send_daily_summary(self):
        """產生並發送每日輿情彙報通知"""
        print("\n[Step 4] 準備發送每日彙報通知...")
        try:
            # 取得最近 24 小時的數據
            stats = database.get_sentiment_stats(days=1)
            
            # 取得負面文章
            neg_result = database.get_articles(sentiment="negative", days=1)
            negative_articles = neg_result["articles"]

            # 偵測最新活動
            promo_keywords = ["活動", "優惠", "新品", "限定", "買一送一", "折扣", "免費"]
            result_today = database.get_articles(days=1, per_page=50)
            promo_articles = []
            seen = set()
            for art in result_today["articles"]:
                if any(kw in art["title"] for kw in promo_keywords):
                    if art["title"] not in seen:
                        promo_articles.append(art)
                        seen.add(art["title"])
            
            # AI 總結
            print("  正在產生今日 AI 綜合總結...")
            summary_articles = result_today["articles"][:30]
            ai_summary = self.analyzer.generate_daily_summary(summary_articles)

            # 各項統計
            trend_stats = database.get_trend_stats()
            source_stats = database.get_source_stats(days=1)

            # 發送
            count = 0
            if self.line_notifier.is_configured:
                self.line_notifier.send_summary(
                    stats=stats,
                    negative_articles=negative_articles,
                    source_stats=source_stats,
                    trend_stats=trend_stats,
                    ai_summary=ai_summary,
                    promo_articles=promo_articles[:3]
                )
                count += 1
            if self.telegram_notifier.is_configured:
                self.telegram_notifier.send_summary(
                    stats=stats,
                    negative_articles=negative_articles,
                    source_stats=source_stats,
                    trend_stats=trend_stats,
                    ai_summary=ai_summary,
                    promo_articles=promo_articles[:3]
                )
                count += 1
            print(f"  ✓ 彙報通知已發送到 {count} 個平台")
        except Exception as e:
            print(f"  ✗ 彙報通知發送失敗: {e}")
