
import database
from analyzer import SentimentAnalyzer
import time
from datetime import datetime
import sys

def process_pending(limit=20):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] 開始處理前 {limit} 篇最新文章...")
    
    analyzer = SentimentAnalyzer()
    
    # 取得最新未分析文章
    unanalyzed = database.get_unanalyzed_articles(limit=limit)
    
    if not unanalyzed:
        print("沒有需要分析的文章。")
        return 0

    print(f"即將處理 {len(unanalyzed)} 篇最新文章。")
    
    processed = 0
    for i, article in enumerate(unanalyzed):
        print(f" [{i+1}/{len(unanalyzed)}] 分析中: {article.get('title', '')[:30]}...")
        
        # 使用目前的設定模型執行分析 (已經在 config.py 設為 gemini-2.0-flash)
        result = analyzer.analyze(
            article.get("title", ""),
            article.get("content", "")
        )
        
        if result.get("status") == "failed":
            print(f"   ✗ 失敗: {result.get('reason')}")
            # 為避免連續失敗浪費 quota，如果失敗過多可考慮跳過
            continue
            
        database.update_sentiment(
            article_id=article["id"],
            sentiment=result["sentiment"],
            score=result["score"],
            reason=result["reason"],
            summary=result["summary"],
        )
        processed += 1
        time.sleep(32) # 間隔 32 秒以避開 2.5-Flash 極低頻率限制 (預覽版通常設限較嚴)
        
    print(f"完成！成功分析了 {processed} 篇文章。")
    return processed

if __name__ == "__main__":
    count = 20
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    process_pending(count)
