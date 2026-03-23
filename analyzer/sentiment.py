"""
LLM 情感分析模組
支援 OpenAI GPT 與 Google Gemini
"""
import json
import re

import config


SENTIMENT_PROMPT = """你是一個品牌輿情分析專家。請分析以下關於「麥當勞」的文章，判斷其情感傾向。

請以 JSON 格式回覆，包含以下欄位：
- sentiment: "positive"（正面）、"negative"（負面）或 "neutral"（中立/無影響）
- score: 情感分數，-1.0（最負面）到 1.0（最正面），0 為中立
- reason: 簡短說明判斷原因（繁體中文，30字以內）
- summary: 文章摘要（繁體中文，50字以內）

只回覆 JSON，不要加其他文字。

文章標題：{title}
文章內容：{content}
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
        """批次分析多篇文章。"""
        import time
        results = []
        for i, article in enumerate(articles):
            print(f"  分析中 ({i+1}/{len(articles)}): {article.get('title', '')[:30]}...")
            
            # 重試機制 (處理 Quota 或網路延遲)
            max_retries = 2
            for attempt in range(max_retries):
                result = self.analyze(
                    article.get("title", ""),
                    article.get("content", "")
                )
                
                # 如果是配額限制，多等一下再重試
                if "Quota" in str(result.get("reason", "")) and attempt < max_retries - 1:
                    print(f"    ⚠️ 觸發頻率限制，等待 30 秒後重試... ({attempt+1}/{max_retries})")
                    time.sleep(30)
                    continue
                break
                
            result["article_id"] = article.get("id")
            results.append(result)
            time.sleep(6)  # 提高間隔到 6 秒 (10 RPM)，確保不觸發 Free Tier 限制
        return results

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
        models_to_try = [config.GEMINI_MODEL, "gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-2.0-flash"]
        last_error = None
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
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
                        max_output_tokens=500,
                    )
                )
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
        """解析 LLM 回應的 JSON"""
        text = text.strip()
        # 清除可能的 markdown code block
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])

        # 嘗試直接 parse
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # 嘗試用 regex 擷取 JSON
            match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    return {
                        "sentiment": "neutral",
                        "score": 0.0,
                        "reason": "LLM 回應格式無法解析",
                        "summary": text[:50],
                        "status": "failed",
                    }
            else:
                return {
                    "sentiment": "neutral",
                    "score": 0.0,
                    "reason": "LLM 回應格式無法解析",
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
