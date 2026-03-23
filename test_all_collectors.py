from collectors import (
    GoogleNewsCollector, PTTCollector, DcardCollector,
    FacebookCollector, InstagramCollector, GoogleReviewsCollector,
    TavilySearchCollector, DDGSearchCollector,
)
import config

def test_collectors():
    collectors = [
        GoogleNewsCollector(),
        PTTCollector(),
        DcardCollector(),
        FacebookCollector(),
        InstagramCollector(),
        GoogleReviewsCollector(),
        TavilySearchCollector(),
        DDGSearchCollector(),
    ]
    
    keywords = ["麥當勞"]
    print(f"=== 搜集器測試 (關鍵字: {keywords[0]}) ===")
    for c in collectors:
        try:
            print(f"正在測試: {c.name}...")
            items = c.collect(keywords)
            print(f"  ✅ {c.name} 搜集成功: {len(items)} 篇文章")
            if items:
                print(f"    範例標題: {items[0]['title'][:50]}")
        except Exception as e:
            print(f"  ❌ {c.name} 搜集失敗: {e}")
        print("-" * 30)

if __name__ == "__main__":
    test_collectors()
