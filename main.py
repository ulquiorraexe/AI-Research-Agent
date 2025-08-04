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
- Use the sources listed below as a reference and prioritize them.
- If needed, you may also include general publicly available data that you believe is reliable.
- Do **not** add any explanations, analysis, or personal commentary — only the structured report.
- Use **today’s date** for all findings.
- If any section has no updates, write: “There is no new update in this category today.”
- In section 7, include download count **within Turkey** where available.
- Do not repeat the same item across multiple sections.

You may use content **only** from the following sources:

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

Your response must include **all 7 sections in full**, clearly numbered and titled as above.
Return the report only — no introduction, no closing note.
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
Do not stop midway. Ensure all categories are included before you finish.
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
        response = llm.invoke(messages)
        raw_output = response.content.strip()

        if not raw_output:
            print("Boş çıktı alındı. İşlem yapılmıyor.")
            return

        # 7 başlık içerip içermediğini kontrol et
        expected_sections = ["1)", "2)", "3)", "4)", "5)", "6)", "7)"]
        if not all(section in raw_output for section in expected_sections):
            print("Beklenen 7 başlık bulunamadı. Ham çıktı aşağıda:")
            print(raw_output)
            return

        previous_raw = load_previous_text()

        # İlk çalıştırma
        if not previous_raw.strip():
            if "There is no new update" in raw_output:
                send_to_telegram("Bugün yeni bir gelişme yok.", bot_token=telegram_token, chat_id=telegram_chat_id)
                print("İlk çalıştırma: Güncelleme yok mesajı gönderildi.")
            else:
                send_to_telegram(raw_output, bot_token=telegram_token, chat_id=telegram_chat_id)
                print("İlk çalıştırma: Tam rapor gönderildi.")
            save_current_text(raw_output, "previous_output.txt")
            save_current_text(raw_output + "\n\n---\n\n", "research_output.txt")
            return

        # Önceki ile fark var mı?
        if has_new_data(raw_output, previous_raw):
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
            send_to_telegram("Bugün yeni bir gelişme yok.", bot_token=telegram_token, chat_id=telegram_chat_id)
            print("Yeni gelişme yok mesajı gönderildi.")

    except Exception as e:
        print("Genel hata:", e)

if __name__ == "__main__":
    main()
