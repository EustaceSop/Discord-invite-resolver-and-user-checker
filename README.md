# Discord User & Invite Lookup Tool

這是一個基於 discord.py 開發的開源工具，旨在幫助社群管理員或開發者深入解析 Discord 邀請連結以及使用者 ID 的背後資訊。

## 🌟 主要功能

- **邀請連結深度解析**：透過 `/lookup` 指令，自動提取邀請連結建立者的詳細 Profile、目標伺服器名稱及成員總數。
- **使用者 ID 查詢**：透過 `/id_lookup` 指令，直接使用 18 位 ID 獲取使用者的 Bio、橫幅、勳章及帳號壽命。
- **自動語言偵測**：界面支援繁體中文與英文，根據使用者客戶端語系自動切換。
- **詳細資訊展示**：
    - 帳號建立精確時間（本地化時區顯示）。
    - 帳號年資計算（例如：1.6 年）。
    - 勳章識別（Staff, Early Supporter, House Balance 等）。
    - 伺服器標籤 (Clan Tag) 與頭像裝飾框連結。
- **高併發保護**：內建 Semaphore 號誌機制，限制同時 API 請求數，防止機器人 IP 被 Discord 封鎖。

## 🛠 安裝與設定

1. **環境準備**：
   確保你的環境已安裝 Python 3.8+。

2. **安裝依賴庫**：
   `pip install discord.py aiohttp python-dotenv`
3. **安全性配置 (推薦)**：
   為了避免 Token 外洩，請在專案根目錄建立 .env 檔案：
   `DISCORD_TOKEN=你的機器人Token`
5. **運行**：
   `python bot.py`
## 📋 指令清單指
| 指令 | 說明 |
| :--- | :--- |
| `/lookup <url>` | 解析邀請連結，回傳建立者與伺服器資訊 |
| `/id_lookup <id>` | 直接查詢指定 ID 的使用者詳細資料 |

## ⚙️ 核心開發邏輯
- 併發控制：使用 asyncio.Semaphore(5) 確保機器人不會在瞬間發出過量請求。
- 時間處理：利用 Snowflake ID 位元運算還原建立時間，並使用 Discord <t:timestamp:F> 語法達成時區自適應。
- 錯誤處理：針對指令冷卻（Cooldown）與無效 ID 進行了人性化的錯誤提示。

## ⚠️ 免責聲明
本專案僅供技術研究，請勿用於騷擾他人或違反 Discord 服務條款。
---
`文擋及部分代碼由Gemini協助撰寫`
