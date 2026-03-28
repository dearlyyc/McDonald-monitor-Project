import json
import re
import warnings
import time

# 靜音 google-generativeai 的過期警告
warnings.filterwarnings("ignore", category=FutureWarning)

import logging
import config

logger = logging.getLogger(__name__)


SENTIMENT_PROMPT = """你是一個品牌輿情分析專家。請分析以下關於「麥當勞」的文章，判斷其情感傾向。

請以 JSON 格式回覆，包含以下欄位：
- sentiment: "positive"（正面）、"negative"（負面）或 "neutral"（中立/無影響）
- score: 情感分數，-1.0（最負面）到 1.0（最正面），0 為中立
- reason: 簡短說明判斷原因（繁體中文，30字以內）
- summary: 文章摘要（繁體中文，50字以內）
- is_outdated: 根據內容判斷這是否為超過一個月以上的陳舊往事/舊聞 (boolean: true/false)

只回覆 JSON，不要加其他文字。
如果你判定為陳舊新聞 (is_outdated: true)，請將 sentiment 設為 "neutral"，score 設為 0。

文章標題：{title}
文章內容：{content}
"""

BATCH_PROMPT = """你是一個品牌輿情分析專家。請分析以下多篇關於「麥當勞」的文章，判斷其情感傾向。

請針對每篇文章回覆一個 JSON 物件，並將所有物件放入一個 JSON 列表 (List) 中回覆。
每個物件包含：
- id: 文章產生的唯一 ID (我們會提供給你)
- sentiment: "positive"（正面）、"negative"（負面）或 "neutral"（中立/無影響）
- score: 情感分數，-1.0（最負面）到 1.0（最正面），0 為中立
- reason: 簡短說明判斷原因（繁體中文，30字以內）
- summary: 文章摘要（繁體中文，50字以內）
- is_outdated: 是否為陳舊舊聞 (true/false)

只回覆 JSON 列表，不要加其他文字標題或說明。如果判定為舊聞，請將 sentiment 設為 "neutral"。

待分析文章列表：
{articles_text}
"""


class SentimentAnalyzer:
    """LLM 情感分析器"""

    def __init__(self):
        self.provider = config.LLM_PROVIDER

    def analyze(self, title: str, content: str) -> dict:
        """
        分析單篇文章的情感傾向。
        """
        # 如果文章標題和內容都為空，直接回傳中立
        if not title.strip() and not content.strip():
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "reason": "無內容可分析",
                "summary": "空白文章",
            }

        prompt = SENTIMENT_PROMPT.format(
            title=title,
            content=content[:3000]
        )

        try:
            if self.provider == "openai":
                response_text = self._call_openai(prompt)
            elif self.provider == "gemini":
                response_text = self._call_gemini(prompt)
            else:
                raise ValueError(f"不支援的 LLM 提供商: {self.provider}")

            return self._parse_response(response_text)
        except Exception as e:
            print(f"[Analyzer] 分析失敗: {e}")
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "reason": f"分析失敗: {str(e)[:50]}",
                "summary": title[:50],
                "status": "failed"
            }

    def analyze_batch(self, articles: list[dict]) -> list[dict]:
        """批量分析多篇文章，顯著提升速度。"""
        import time
        results = []
        batch_size = 5  # 減少每組預設數量以避開 2.5 系列可能的更嚴格限制
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i : i + batch_size]
            print(f"  正在分析第 {i//batch_size + 1} 組 ({i+1}~{min(i+batch_size, len(articles))}/{len(articles)})...")
            
            # 準備批量資料
            articles_text = ""
            for art in batch:
                title = art.get("title", "無標題")
                content = art.get("content", "")[:500] # 批量時限制每篇內容長度，避免超出 Token
                articles_text += f"---\nID: {art.get('id')}\n標題: {title}\n內容: {content}\n"

            prompt = BATCH_PROMPT.format(articles_text=articles_text)
            
            # 指數退避重試機制 (Exponential Backoff)
            response_text = None
            max_retries = 4
            for attempt in range(max_retries):
                try:
                    if self.provider == "gemini":
                        response_text = self._call_gemini(prompt)
                        # Debug: 列印前 100 字回應
                        if response_text:
                            print(f"    [Success] 已獲得回應，內容長度: {len(response_text)} 字")
                        else:
                            print("    [Warning] 回應為空")
                    else:
                        response_text = self._call_openai(prompt)
                    break
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "ResourceExhausted" in error_msg or "Quota" in error_msg:
                        wait_time = 20 * (2 ** attempt)  # 20秒, 40秒, 80秒...
                        print(f"    ⚠️ 觸發 API 頻率限制 (Rate Limit)，等待 {wait_time} 秒後重試... ({attempt+1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        print(f"    [Fail] 批量呼叫發生未預期錯誤: {e}")
                        break
            
            if response_text:
                try:
                    # 解析列表
                    batch_results = self._parse_batch_response(response_text)
                    for res in batch_results:
                        res["article_id"] = res.get("id")
                        results.append(res)
                except Exception as e:
                    print(f"    [Fail] 解析批量結果失敗: {e}")
            
            # 任務間插入更強的靜態冷卻時間
            wait_between = 15
            print(f"    ↳ 此組完成，冷卻 {wait_between} 秒...")
            time.sleep(wait_between) 

        return results

    def _parse_batch_response(self, text: str) -> list[dict]:
        """解析批量回應的 JSON 列表，增強穩定性"""
        if not text or not text.strip():
            print("[Analyzer] 批量回應內容為空")
            return []
            
        text = text.strip()
        
        # 尋找第一個 [ 和最後一個 ]
        start = text.find('[')
        end = text.rfind(']')
        
        if start != -1 and end != -1 and end > start:
            clean_text = text[start:end+1]
        else:
            # 如果找不到列表，尋找單個物件並包裝
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                clean_text = f"[{text[start:end+1]}]"
            else:
                clean_text = text

        try:
            results = json.loads(clean_text)
            if isinstance(results, list):
                return results
            return [results]
        except json.JSONDecodeError as e:
            print(f"[Analyzer] 批量解析 JSON 失敗: {e}")
            print(f"--- 嘗試解析的片段 (前 100 字) ---")
            print(clean_text[:100])
            print("-----------------------------------")
            return []

    def generate_daily_summary(self, articles: list[dict]) -> str:
        """產生每日輿情綜合歸納總結。"""
        if not articles:
            return "今日暫無新的輿情資料可供總結。"

        content_lines = []
        for i, article in enumerate(articles[:30]):
            title = article.get("title", "")
            summary = article.get("summary", "")
            sentiment = article.get("sentiment", "neutral")
            content_lines.append(f"[{sentiment}] 標題：{title} - 摘要：{summary}")

        combined_text = "\n".join(content_lines)
        prompt = (
            "你是一個品牌輿情公關專家。請根據以下「麥當勞」今日的社群與新聞輿情資料，"
            "自動濃縮成「一小段重點精華總結」（約100字以內），說明今日網友主要討論的話題、"
            "為何給出正面評價，或針對什麼有抱怨聲浪。\n\n"
            "請直接回覆總結內容，以平鋪直敘不浮誇的專業語氣，不要引言或問候語。\n\n"
            f"輿情資料：\n{combined_text[:6000]}"
        )

        try:
            if self.provider == "openai":
                return self._call_openai(prompt)
            elif self.provider == "gemini":
                return self._call_gemini(prompt)
            return "不支援的 LLM"
        except Exception as e:
            print(f"[Analyzer] 總結失敗: {e}")
            return "今日輿情總結產生失敗。"

    def _call_openai(self, prompt: str) -> str:
        """呼叫 OpenAI API"""
        from openai import OpenAI

        if not config.OPENAI_API_KEY:
            raise ValueError("未設定 OPENAI_API_KEY 環境變數")

        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是品牌輿情分析專家。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        return response.choices[0].message.content

    def _call_gemini(self, prompt: str) -> str:
        """呼叫 Google Gemini API"""
        import google.generativeai as genai

        if not config.GEMINI_API_KEY:
            raise ValueError("未設定 GEMINI_API_KEY 環境變數")

        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # 嘗試模型列表 (按照優先順序)
        models_to_try = [config.GEMINI_MODEL, "gemini-2.0-flash", "gemini-1.5-flash"]
        last_error = None
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                # 設定更寬鬆的安全過濾 (適用於輿情分析)
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
                
                response = model.generate_content(
                    prompt,
                    safety_settings=safety_settings,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=1000, # 批量分析需要更長的輸出空間
                    )
                )
                
                if not response.text:
                    # 檢查是否被安全攔截
                    if hasattr(response, 'candidates') and response.candidates[0].finish_reason != 1:
                        print(f"    [Warning] Gemini 攔截了回應 (原因: {response.candidates[0].finish_reason})")
                    return ""
                    
                return response.text
            except Exception as e:
                # 只有當錯誤是 404 (找不到模型) 才繼續試下一個
                if "404" in str(e):
                    last_error = e
                    continue
                # 429 或其他錯誤則拋出 (讓 batch 級別處理重試)
                raise e

        # 如果所有模型都試過且都 404
        raise last_error if last_error else ValueError("找不到可用的 Gemini 模型 (404)")

    def _parse_response(self, text: str) -> dict:
        """解析 LLM 回應的 JSON, 具備更強的容錯能力"""
        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "reason": "回應為空",
                "summary": "無內容",
            }
            
        text = text.strip()
        
        # 尋找第一個 { 和最後一個 }
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            clean_text = text[start:end+1]
        else:
            clean_text = text

        # 嘗試直接 parse
        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError:
            print(f"[Analyzer] JSON 解析失敗: {clean_text[:100]}...")
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "reason": "LLM 回應格式錯誤",
                "summary": text[:50],
                "status": "failed",
            }

        # 驗證並標準化
        valid_sentiments = {"positive", "negative", "neutral"}
        sentiment = data.get("sentiment", "neutral")
        if sentiment not in valid_sentiments:
            sentiment = "neutral"

        score = float(data.get("score", 0.0))
        score = max(-1.0, min(1.0, score))

        return {
            "sentiment": sentiment,
            "score": score,
            "reason": str(data.get("reason", ""))[:100],
            "summary": str(data.get("summary", ""))[:200],
        }
