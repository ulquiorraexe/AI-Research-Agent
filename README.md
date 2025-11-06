# 🎮 Turkish Game Industry Daily Research Bot

This project automatically generates a **daily AI-powered research report** focused on the **Turkish game development ecosystem**.  
It uses **LangChain** and the **DeepSeek R1** model (via [OpenRouter](https://openrouter.ai)) to collect structured insights from verified gaming sources and sends daily updates to a **Telegram channel**.

---

## 🧠 Features

- Generates a **7-section structured report** every day:
  1. New Turkish game releases and developer announcements  
  2. Turkish game market trends and sales data  
  3. Game jams in Turkey or involving Turkish participants  
  4. Community insights from Turkish Twitch and YouTube creators  
  5. Technological developments impacting the Turkish gaming industry  
  6. Highlights from relevant RSS feeds  
  7. Currently popular games in Turkey  

- Compares each new report with the previous one  
- Sends updates to Telegram **only when new data is detected**  
- Prevents redundant or repeated information  
- Automatically stores and updates daily outputs  

---

## ⚙️ Installation

```bash
git clone https://github.com/yourusername/turkish-game-research-bot.git
cd turkish-game-research-bot
pip install -r requirements.txt
```
## 🔑 Environment Variables

Create a .env file in the project root and add the following:
```bash
TOGETHER_API_KEY=your_openrouter_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

## 🚀 Usage

Run the script manually:
```bash
python main.py
```
Or schedule it daily with a GitHub Action or cron job to automate daily research and Telegram updates.

## 📂 File Structure

```bash
.
├── main.py               # Main script that generates and sends reports
├── utils.py              # Helper functions (file handling, Telegram, comparison)
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
├── previous_output.txt   # Stores the previous day's report
└── research_output.txt   # Stores all research history
```

