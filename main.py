from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from utils import (
    load_previous_text,
    save_current_text,
    has_new_data,
    prepare_and_send_message,
    send_to_telegram
)

load_dotenv()

api_key = os.getenv("TOGETHER_API_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

system_prompt = """
You are a research assistant focusing exclusively on the Turkish game development ecosystem.

Your task is to generate a detailed and structured report in exactly 7 numbered sections:

1) New Turkish game releases and developer announcements  
2) Turkish game market trends and sales data  
3) Game jams in Turkey or with Turkish participants  
4) Community opinions from Turkish Twitch and YouTube creators  
5) Technological developments impacting the Turkish gaming industry  
6) Relevant RSS feed highlights  
7) Currently popular Turkish games in the Turkish gaming market

Instructions for all sections:

- Include **at least 10 unique and detailed items** (e.g., news, events, statistics).
- Every item **must include a source** in this format: `(Source: Name or URL)`.
- Use only the sources listed below. Do **not hallucinate**.
- Do **not** add any explanations, analysis, or personal commentary — only the structured report.
- Use **today’s date** for all findings.
- If any section has no updates, write: “There is no new update in this category today.”
- In section 7, include download count **within Turkey** where available.
- Do not repeat the same item across multiple sections.
- Do not stop generation until all 7 sections are completed.

Sources you may use:

- GamesIndustry.biz  
- IGN  
- Game Developer  
- Kotaku  
- Polygon  
- SteamDB  
- Steam Charts  
- Global Game Jam  
- Istanbul Game Festival  
- Turkish Game Developer Conference  
- Twitch (Turkish streamers)  
- YouTube (Turkish gaming creators)  
- Newzoo  
- VRFocus  
"""

query = """
Your task is to generate a detailed, structured report in 7 numbered sections:

1) New Turkish game releases and developer announcements  
2) Turkish game market trends and sales data  
3) Game jams in Turkey or with Turkish participants  
4) Community opinions from Turkish Twitch and YouTube creators  
5) Technological developments impacting the Turkish gaming industry  
6) Relevant RSS feed highlights  
7) Currently popular Turkish games in the Turkish gaming market

Each section must begin with its number and title exactly as listed, followed by your findings.
If there is no new information in a section, simply say: 'There is no new update in this category today.'

After completing the full 7-category report, respond with everything in one single output. 
**Do not stop midway. Do not omit any section.**
"""

llm = ChatOpenAI(
    openai_api_key=api_key,
    openai_api_base="https://openrouter.ai/api/v1",
    model="deepseek/deepseek-r1-0528:free",
    temperature=0.0,
    max_tokens=4096,
)

def main():
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]

        raw_output = ""
        expected_sections = ["1)", "2)", "3)", "4)", "5)", "6)", "7)"]

        for attempt in range(3):
            print(f"Deneme {attempt + 1}...")
            response = llm.invoke(messages)
            raw_output = response.content.strip()

            if not raw_output:
                print("Boş çıktı alındı.")
                continue

            if all(section in raw_output for section in expected_sections):
                print("Tüm başlıklar bulundu.")
                break
            else:
                print("Eksik başlık var, tekrar deneniyor...")
        else:
            print("3 denemeden sonra başlıklar tamamlanamadı. Ham çıktı:")
            print(raw_output)
            return

        previous_raw = load_previous_text()

        # Bütün satırlar "There is no new update" içeriyor mu?
        def is_all_sections_empty(text):
            return all(
                "There is no new update" in line
                for line in text.splitlines()
                if line.strip() and any(s in line for s in expected_sections)
            )

        all_sections_empty = is_all_sections_empty(raw_output)

        # İlk çalıştırma
        if not previous_raw.strip():
            if all_sections_empty:
                print("İlk çalıştırma: Rapor boş, mesaj gönderilmiyor.")
            else:
                send_to_telegram(raw_output, bot_token=telegram_token, chat_id=telegram_chat_id)
                print("İlk çalıştırma: Tam rapor gönderildi.")
            save_current_text(raw_output, "previous_output.txt")
            save_current_text(raw_output + "\n\n---\n\n", "research_output.txt")
            return

        # Önceki ile fark var mı?
        if has_new_data(raw_output, previous_raw):
            if all_sections_empty:
                print("Yeni çıktı boş, mesaj gönderilmiyor.")
            else:
                success = prepare_and_send_message(
                    new_output=raw_output,
                    previous_output=previous_raw,
                    bot_token=telegram_token,
                    chat_id=telegram_chat_id
                )
                if success:
                    print("Mesaj başarıyla gönderildi ve dosyalar güncellendi.")
                else:
                    print("Mesaj gönderilemedi ama dosyalar güncellendi.")
            save_current_text(raw_output, "previous_output.txt")
            save_current_text(raw_output + "\n\n---\n\n", "research_output.txt")
        else:
            print("Yeni veri yok, hiçbir mesaj gönderilmedi.")

    except Exception as e:
        print("Genel hata:", e)

