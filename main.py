from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, ValidationError
from utils import (
    load_previous_text,
    save_current_text,
    has_new_data,
    prepare_and_send_message,
    send_to_telegram
)

# .env dosyasını yükle
load_dotenv()

api_key = os.getenv("TOGETHER_API_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

class ResearchResponse(BaseModel):
    new_releases: str
    market_trends: str
    game_jams: str
    community_opinions: str
    tech_developments: str
    rss_feeds: str
    popular_games: str 

# Prompt metni
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
- Use **only the sources listed below**. Do **not hallucinate or guess** any information.
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

parser = PydanticOutputParser(pydantic_object=ResearchResponse)

def main():
    try:
        # Mesaj dizisi: önce system sonra human
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]

        # LLM çağrısı
        response = llm(messages)
        raw_output = response.content

        if not raw_output.strip():
            print("Boş çıktı alındı. İşlem yapılmıyor.")
            return

        # Pydantic ile parse etmeye çalış
        try:
            parsed = parser.parse(raw_output)
        except ValidationError as ve:
            print("Parsing sırasında hata oluştu:", ve)
            print("Ham çıktı:", raw_output)
            return

        previous_raw = load_previous_text()
        if not previous_raw.strip():
            # İlk çalıştırma: tam çıktı gönder
            send_to_telegram(raw_output, bot_token=telegram_token, chat_id=telegram_chat_id)
            save_current_text(raw_output, "previous_output.txt")
            save_current_text(raw_output + "\n\n---\n\n", "research_output.txt")
            print("İlk çalıştırma: tam çıktı gönderildi ve dosyalar kaydedildi.")
        elif has_new_data(raw_output, previous_raw):
            # Yeni içerik varsa telegrama gönder ve dosyaları güncelle
            success = prepare_and_send_message(
                new_output=raw_output,
                previous_output=previous_raw,
                bot_token=telegram_token,
                chat_id=telegram_chat_id
            )
            if success:
                print("Mesaj başarıyla gönderildi ve dosyalar güncellendi.")
            else:
                print("Mesaj gönderiminde hata oluştu ama dosyalar güncellendi.")
        else:
            send_to_telegram("Bugün yeni bir gelişme yok.", bot_token=telegram_token, chat_id=telegram_chat_id)

    except Exception as e:
        print("Genel hata:", e)


if __name__ == "__main__":
    main()
