"""
科技晨報處理器 - 篩選並總結今日最重要科技新聞
"""
import json
import logging
from datetime import datetime
import google.generativeai as genai

import config
from collectors.tech_news import TechNewsCollector
from notifier.line_notify import LineNotifier
from notifier.telegram_notify import TelegramNotifier

logger = logging.getLogger(__name__)

TECH_SELECTOR_PROMPT = """你是一個資深科技編輯與產業分析師。下面是從五大科技媒體搜集到的今日新聞列表。
請針對這五個網站：iThome、數位時代、TechNews 科技新報、未來城市、INSIDE 硬塞網路，
**分別從每個網站選出最值得今日閱讀的 5 則新聞** (總共 25 則)。

請將這 25 則新聞彙整成一份高品質的「每日科技晨報」。

對於選出的每一則新聞，請提供（繁體中文）：
- 標題
- 來源網站
- 一句話摘要 (預測對產業的關鍵影響)
- 原始連結

報表結構請按「來源網站」分組排列。

輸出格式必須是 JSON 列表，格式如下：
[
  {{
    "source": "iThome",
    "articles": [
      {{"title": "...", "summary": "...", "url": "..."}},
      ... (共5則)
    ]
  }},
  ... (五個網站各一組)
]

只回覆 JSON，不要有其他文字。

新聞列表：
{news_text}
"""

class TechBriefingAnalyzer:
    def __init__(self):
        if not config.GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY not found in config.")
        genai.configure(api_key=config.GEMINI_API_KEY)
        # 優先使用 config 中的模型設定
        self.model_name = getattr(config, "GEMINI_MODEL", "gemini-1.5-flash")
        self.model = genai.GenerativeModel(self.model_name)

    def run(self):
        print(f"[{datetime.now().isoformat()}] 開始執行科技晨報流程 (使用模型: {self.model_name})...")
        
        # 1. 搜集資料
        collector = TechNewsCollector()
        all_news = collector.collect()
        if not all_news:
            print("未能搜集到任何新聞。")
            return

        # 2. 準備 AI 篩選文字 (均衡分配每個來源的樣本，避免前面的來源佔滿 Token)
        news_by_source = {}
        for n in all_news:
            source = n["source"]
            if source not in news_by_source:
                news_by_source[source] = []
            news_by_source[source].append(n)
        
        balanced_news_lines = []
        for source, articles in news_by_source.items():
            balanced_news_lines.append(f"=== {source} (最新 {len(articles)} 則) ===")
            for i, n in enumerate(articles[:15]): # 每個來源取前 15 則給 AI 挑選
                balanced_news_lines.append(f"ID: {source}_{i} | 標題: {n['title']} | 連結: {n['url']}")
        
        news_text = "\n".join(balanced_news_lines)

        # 3. AI 篩選與總結
        prompt = TECH_SELECTOR_PROMPT.format(news_text=news_text)
        try:
            response = self.model.generate_content(prompt)
            # 解析 JSON
            text = response.text.strip()
            # 容錯處理 Markdown 標記
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0].strip()
            elif text.startswith("```"):
                text = text.split("```")[1].split("```")[0].strip()
            
            top_news = json.loads(text)
        except Exception as e:
            print(f"AI 分析失敗: {e}")
            print(f"原始回應: {response.text if 'response' in locals() else 'None'}")
            return

        # 4. 格式化訊息
        today_str = datetime.now().strftime("%Y-%m-%d")
        msg_lines = [f"🚀 【科技每日洞察】 {today_str}", "---"]
        
        total_count = 0
        for source_group in top_news:
            source_name = source_group.get("source", "未知來源")
            articles = source_group.get("articles", [])
            print(f"  [Debug] {source_name}: 獲取 {len(articles)} 則文章")
            msg_lines.append(f"📌 *【{source_name}】*")
            for i, item in enumerate(articles, 1):
                msg_lines.append(f"  {i}. {item['title']}")
                msg_lines.append(f"     └ {item['summary']}")
                msg_lines.append(f"     🔗 {item['url']}")
                total_count += 1
            msg_lines.append("")
        
        msg_lines.append("---")
        msg_lines.append(f"✅ 共彙整 {total_count} 則重點新聞")
        message = "\n".join(msg_lines)

        print(f"  [Debug] 全文總字數: {len(message)}")

        # 5. 發送通知
        print("正在發送通知...")
        line = LineNotifier()
        
        # 如果訊息太長，分段發送
        if len(message) > 4800:
            print("  [Warning] 訊息過長，正在拆分發送...")
            parts = [message[i:i+4800] for i in range(0, len(message), 4800)]
            for p in parts:
                line.send(p)
        else:
            line.send(message)
        
        tg = TelegramNotifier()
        tg.send(message)
        
        print(f"科技晨報流程執行完畢。共發送 {total_count} 則文章。")

if __name__ == "__main__":
    analyzer = TechBriefingAnalyzer()
    analyzer.run()
