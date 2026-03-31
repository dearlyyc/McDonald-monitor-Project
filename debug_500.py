import database
from datetime import datetime

try:
    print("Testing get_sentiment_stats('yesterday')...")
    res = database.get_sentiment_stats("yesterday")
    print(f"Result: {res}")
except Exception as e:
    import traceback
    traceback.print_exc()
