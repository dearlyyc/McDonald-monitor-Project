import sqlite3
import config

def reset():
    conn = sqlite3.connect(config.DATABASE_PATH)
    # 重置所有包含「分析失敗」字樣或理由為空的「中立」文章
    cursor = conn.execute("""
        UPDATE articles 
        SET analyzed_at = NULL, 
            sentiment = 'neutral', 
            sentiment_reason = NULL, 
            summary = NULL 
        WHERE (sentiment_reason LIKE '%分析失敗%' OR sentiment_reason IS NULL) 
        AND analyzed_at IS NOT NULL
    """)
    conn.commit()
    print(f"已重置 {cursor.rowcount} 篇失敗文章，準備重新分析。")
    conn.close()

if __name__ == "__main__":
    reset()
