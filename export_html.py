import os
import json
import database
from bs4 import BeautifulSoup

def export_to_github_pages():
    print("[Export] 開始打包靜態 HTML...")
    
    # 建立 docs 資料夾供 GitHub Pages 使用
    docs_dir = os.path.join(os.path.dirname(__file__), "docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    # 讀取所需資料 (模擬 API 回應)
    static_data = {}
    
    # 1. Stats
    static_data["/api/stats?days=7"] = database.get_sentiment_stats(days=7)
    
    # 2. Source Stats
    static_data["/api/source-stats?days=7"] = database.get_source_stats(days=7)
    
    # 3. Daily Stats
    for d in [7, 14, 30]:
        static_data[f"/api/daily-stats?days={d}"] = database.get_daily_stats(days=d)
        
    # 4. Logs
    static_data["/api/logs?limit=50"] = database.get_recent_logs(limit=50)
    
    # 5. Articles (預先打包常見的篩選條件：前 3 頁)
    for d in [7, 14, 30]:
        for p in range(1, 4):
            # 所有情感、所有來源
            res = database.get_articles(sentiment="all", source="all", days=d, page=p, per_page=20)
            static_data[f"/api/articles?sentiment=all&source=all&days={d}&page={p}&per_page=20"] = res

    # 讀取原始 HTML
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 注入 Monkey-patch 腳本與資料
    injected_script = f"""
    <script>
        // GitHub Pages 靜態快照資料
        window.GITHUB_PAGES_DATA = {json.dumps(static_data, ensure_ascii=False)};
        
        // 攔截 fetch 請求，直接返回靜態資料
        const originalFetch = window.fetch;
        window.fetch = async (resource, options) => {{
            let url = typeof resource === 'string' ? resource : resource.url;
            
            // 處理查詢參數 URL (網頁上的網址可能因參數順序不同而無法完全匹配字串，這裡做簡單匹配)
            if (window.GITHUB_PAGES_DATA[url]) {{
                return {{
                    ok: true,
                    json: async () => window.GITHUB_PAGES_DATA[url]
                }};
            }}
            
            // 處理 articles 網址重組比對
            if (url.includes('/api/articles?')) {{
                // 若找不到對應快照，回傳空結果避免網頁報錯
                return {{
                    ok: true,
                    json: async () => ({{ articles: [], page: 1, total_pages: 1 }})
                }};
            }}
            
            if (url.includes('/api/run-status')) {{
                return {{ ok: true, json: async () => ({{ is_running: false }}) }};
            }}
            
            if (url.includes('/api/run-now')) {{
                return {{ ok: true, json: async () => ({{ status: "error", message: "靜態備份頁面不支援執行即時分析。" }}) }};
            }}

            return originalFetch(resource, options);
        }};
    </script>
    """
    
    # 將 script 插入到 <head> 區塊的結尾
    html_content = html_content.replace("</head>", injected_script + "\n</head>")
    
    # 為了確保 GitHub Pages 吃到正確的 CSS / JS 路徑，我們直接將路徑相對化
    # <link rel="stylesheet" href="/static/css/style.css"> -> href="static/css/style.css"
    html_content = html_content.replace('href="/static/', 'href="static/')
    html_content = html_content.replace('src="/static/', 'src="static/')
    
    # 將結果寫入 docs/index.html
    docs_index_path = os.path.join(docs_dir, "index.html")
    with open(docs_index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("  ✓ docs/index.html 產生成功！")

    # 複製 static 資料夾到 docs 內
    import shutil
    static_src = os.path.join(os.path.dirname(__file__), "static")
    static_dst = os.path.join(docs_dir, "static")
    if os.path.exists(static_dst):
        shutil.rmtree(static_dst)
    shutil.copytree(static_src, static_dst)
    print("  ✓ docs/static 資源複製成功！")
    print("🎉 靜態匯出完成！")

if __name__ == "__main__":
    export_to_github_pages()
