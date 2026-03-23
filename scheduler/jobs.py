import os
import json
import shutil
import subprocess
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

import config
import database
from collectors import (
    GoogleNewsCollector, FacebookCollector, InstagramCollector,
    GoogleReviewsCollector, TavilySearchCollector, DDGSearchCollector,
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
            # 方案 B：暫時關閉會消耗 Apify 月度 $5 額度的搜集器（等待下個月額度重置後再打開）
            # FacebookCollector(),
            # InstagramCollector(),
            # GoogleReviewsCollector(),
            TavilySearchCollector(),
            DDGSearchCollector(),
        ]
        self.analyzer = SentimentAnalyzer()
        self.line_notifier = LineNotifier()
        self.telegram_notifier = TelegramNotifier()
        self.is_running = False

    def start(self):
        """啟動排程器 (僅保留每日早上 10:00 的主動搜尋與通知)"""
        self.scheduler.add_job(
            self.run_monitor_cycle,
            "cron",
            hour=config.SCHEDULE_CRON_HOUR,
            minute=config.SCHEDULE_CRON_MINUTE,
            args=[True], # 觸發搜尋 + 發送消息
            id="daily_main_cycle",
            name=f"每日彙報與搜尋 ({config.SCHEDULE_CRON_HOUR}:00)",
            misfire_grace_time=3600*24,
            coalesce=True
        )
        # 新增備份任務：每日下午 2:00 (14:00) 備份到 GitHub
        self.scheduler.add_job(
            self.backup_to_github,
            "cron",
            hour=14,
            minute=0,
            id="daily_github_backup",
            name="每日 GitHub 備份任務 (14:00)",
            misfire_grace_time=3600*24,
            coalesce=True
        )
        print(f"[Scheduler] 已啟動每日 10:00 的彙報任務與 14:00 的 GitHub 備份任務")
        self.scheduler.start()

    def backup_to_github(self):
        """執行雙重備份 (GitHub + 本地)，並額外為 Obsidian 生成當日報告筆記"""
        print(f"\n[Backup] {datetime.now().isoformat()} - 開始執行雙重備份與筆記生成任務...")
        
        obsidian_path = r"D:\OBSIDIAN_Vault\McDonald monitor Project"
        if not os.path.exists(obsidian_path):
            os.makedirs(obsidian_path, exist_ok=True)

        try:
            # 0. 產生 GitHub Pages 靜態網頁 (.html)
            print("  正在匯出 GitHub Pages 靜態快照...")
            try:
                from export_html import export_to_github_pages
                export_to_github_pages()
            except Exception as e:
                print(f"  [Fail] 靜態頁面匯出失敗: {e}")

            # 1. 生成今日筆記 (Markdown)
            self._generate_obsidian_report(obsidian_path)
            
            # 2. 本地備份全專案 (讓 Obsidian 備份與 GitHub 完全一致，排除不必要的暫存檔)
            print("  正在將全專案複製到 Obsidian 本地庫...")
            project_root = os.path.dirname(os.path.dirname(__file__)) # 取得上一層的專案根目錄
            shutil.copytree(
                project_root, 
                obsidian_path, 
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('venv', '.git', '__pycache__', 'node_modules', '*.pyc', 'launch_silent.vbs')
            )
            print(f"  [OK] 本地全專案備份完成")

            # 3. GitHub 備份
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            commit_msg = f"每日自動備份: {datetime.now().strftime('%Y-%m-%d')}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=False, capture_output=True)
            subprocess.run(["git", "push"], check=True, capture_output=True)
            print("  [OK] GitHub 備份成功！")
        except Exception as e:
            print(f"  [Fail] 備份任務中斷: {e}")

    def _generate_obsidian_report(self, dest_path):
        """自動生成 Obsidian 格式的輿情報告，並存入專屬的報告資料夾"""
        import os
        from datetime import datetime
        print("  正在生成 Obsidian 今日報告...")
        
        # 建立專屬的「每日報告」子資料夾
        report_dir = os.path.join(dest_path, "每日報告")
        os.makedirs(report_dir, exist_ok=True)
        
        # 取得最新一筆監控記錄
        logs = database.get_recent_logs(limit=1)
        if not logs:
            return
        
        log = logs[0]
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_name = f"麥當勞輿情報告_{date_str}.md"
        file_path = os.path.join(report_dir, file_name)
        
        # 取得今日負面文章 (用於筆記列表)
        from datetime import date
        articles_data = database.get_articles(sentiment="negative", days=1, per_page=10)
        neg_articles = articles_data.get("articles", [])

        # 這裡由於無法直接取得 AI Summary 文字，我們從 articles 的最後一篇摘要來展示，或者從 DB 重新獲取
        # 實務上我們從 unanalyzed 為空的文章中抓取最近的一筆摘要作為代表
        content = f"""# 🍔 麥當勞輿情報告 - {date_str}

## 📊 數據統計
- **總搜集篇數**: {log.get('total_collected', 0)}
- 🟢 **正面**: {log.get('positive_count', 0)}
- 🔴 **負面**: {log.get('negative_count', 0)}
- ⚪ **中立**: {log.get('neutral_count', 0)}

## ⚠️ 今日負面關注
"""
        if not neg_articles:
            content += "- 今日暫無重大負面消息。\n"
        else:
            for art in neg_articles:
                content += f"- **[{art['source']}]** {art['title']}  \n  [連結]({art['url']})  \n"

        content += f"\n--- \n*本筆記由 McDonald Monitor 系統於 {datetime.now().strftime('%H:%M')} 自動生成。*"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [OK] 報告已存至 Obsidian: {file_name}")

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
                    print(f"  [Fail] {collector.name} 搜集失敗: {e}")

            new_count = 0
            for article in all_articles:
                if database.insert_article(article):
                    new_count += 1
            log["total_collected"] = new_count
            print(f"  [OK] 新增 {new_count} 篇文章")

            # Step 3: 情感分析 (限制最新 40 篇以提昇速度)
            print("\n[Step 3] 情感分析...")
            unanalyzed = database.get_unanalyzed_articles(limit=40)
            if unanalyzed:
                print(f"  正在分析最新 {len(unanalyzed)} 篇輿情...")
                # 批量呼叫並即時存檔
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
                print(f"  [OK] 完成 {analyzed_count} 篇文章分析")
                print(f"  [OK] 成功分析了 {analyzed_count} 篇文章")

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
            print(f"  [OK] 彙報通知已發送到 {count} 個平台")
        except Exception as e:
            print(f"  [Fail] 彙報通知發送失敗: {e}")
