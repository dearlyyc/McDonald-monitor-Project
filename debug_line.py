import sys, os
sys.path.append(os.getcwd())
from notifier.line_notify import LineNotifier
import config

stats = {"total": 10, "positive": 2, "negative": 1, "neutral": 7}
neg = [{"title": "麥當勞壞掉了"}]
ai = "目前麥當勞一切正常，除了我的測試訊息。"

line = LineNotifier()
print(f"Configured: {line.is_configured}")
res = line.send_summary(stats=stats, negative_articles=neg, ai_summary=ai)
print(f"Result: {res}")
