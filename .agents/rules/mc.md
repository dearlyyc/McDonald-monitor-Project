---
trigger: always_on
---

# 麥當勞品牌輿情監控系統 - 專案規則

## 專案概述

本專案是一套自動化品牌輿情監控系統，流程為：**搜集 → 分析 → 報告 → 通知 → 排程**。

## 技術架構

| 項目   | 技術                                                                                  |
| ------ | ------------------------------------------------------------------------------------- |
| 語言   | Python 3.x                                                                            |
| 後端   | Flask                                                                                 |
| 前端   | HTML + CSS + JavaScript（Vanilla）                                                    |
| 資料庫 | SQLite（`mcdonalds_monitor.db`）                                                    |
| 排程   | APScheduler（cron 模式，每日 07:00）                                                  |
| LLM    | **Google Gemini**（`gemini-2.0-flash`），透過環境變數 `GEMINI_API_KEY` 設定 |
| 通知   | Line Notify + Telegram Bot（框架已建立，Token 待填入）                                |

## 搜集來源（共 6 個搜集器）

1. **Google News** — RSS Feed（`collectors/google_news.py`）
2. **PTT** — 網頁爬蟲，看板：Gossiping、fastfood、Lifeismoney（`collectors/ptt.py`）
3. **Dcard** — 搜尋 API（`collectors/dcard.py`）
4. **Facebook** — 公開粉絲頁爬蟲（`collectors/facebook.py`）
5. **Instagram** — 公開帳號 + hashtag 資訊（`collectors/instagram.py`）
6. **Google 評論** — 透過搜尋取得評論摘要（`collectors/google_reviews.py`）

## 搜集關鍵字

- 預設關鍵字：`麥當勞`、`McDonald's`、`McDonalds`
- 所有關鍵字集中在 `config.py` 的 `SEARCH_KEYWORDS` 管理

## LLM 情感分析

- 使用 **Google Gemini** 作為 LLM 提供商
- 分類三種情感：**正面（positive）**、**負面（negative）**、**中立（neutral）**
- 每篇文章分析輸出：情感分類、分數（-1.0 ~ 1.0）、判斷原因、摘要
- 分析邏輯位於 `analyzer/sentiment.py`

## 排程規則

- **模式**：cron 定時排程
- **執行時間**：每天早上 **07:00**
- 可透過環境變數 `SCHEDULE_CRON_HOUR` / `SCHEDULE_CRON_MINUTE` 調整
- 支援手動觸發（Web UI「立即執行」按鈕 或 `/api/run-now` API）

## 通知規則

- Line Notify Token → 環境變數 `LINE_NOTIFY_TOKEN`
- Telegram Bot Token → 環境變數 `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`
- 觸發條件：出現負面新聞時通知，或每次排程完成後發送摘要

## 設計規範

- **前端主題**：暗色模式（Dark Theme）
- **品牌色**：紅色 `#DA291C` / 黃色 `#FFC72C`
- **字體**：Noto Sans TC + Inter
- **響應式設計**：支援桌面、平板、手機

## 程式碼規範

- 所有設定集中管理於 `config.py`，支援環境變數覆蓋
- 敏感資訊（API Key、Token）**禁止寫死在程式碼中**，一律使用環境變數
- 搜集器統一繼承 `BaseCollector`，實作 `collect()` 方法
- 文章資料統一格式：`{ title, content, source, url, published_at, raw_data }`
- 資料庫操作統一透過 `database.py` 的函式，不直接在其他模組中操作 SQL
- 繁體中文為主要介面語言

## 環境變數清單

```
GEMINI_API_KEY=<your-gemini-api-key>
LLM_PROVIDER=gemini
LINE_NOTIFY_TOKEN=<your-line-token>
TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
TELEGRAM_CHAT_ID=<your-telegram-chat-id>
SCHEDULE_CRON_HOUR=7
SCHEDULE_CRON_MINUTE=0
SECRET_KEY=<your-flask-secret-key>
```