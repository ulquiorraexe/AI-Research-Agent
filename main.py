from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, ValidationError
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import save_tool, save_to_txt
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

llm = ChatOpenAI(
    openai_api_key=api_key,
    openai_api_base="https://api.together.xyz/v1",
    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.0,
    max_completion_tokens=4096
)
parser = PydanticOutputParser(pydantic_object=ResearchResponse)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system", """
            You are a research assistant focusing on the Turkish game development ecosystem.

            Your task is to generate a detailed, structured report in 7 numbered sections:

            1) New Turkish game releases and developer announcements  
            2) Turkish game market trends and sales data  
            3) Game jams in Turkey or with Turkish participants  
            4) Community opinions from Turkish Twitch and YouTube creators  
            5) Technological developments impacting the Turkish gaming industry  
            6) Relevant RSS feed highlights  
            7) Currently popular Turkish games in the Turkish gaming market

            For each section:

            - Include **at least 10 detailed items** (news, events, stats, etc.).
            - After each item, include the **source** in the format: `(Source: Name or URL)`.
            - Write clearly, without unnecessary repetition or generic phrases.
            - Do **not** include extra explanation, just the report.
            - Do **not** break the numbered structure.

            Only use these sources for your answers:

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

            Return only the structured report in this 7-part format, no other commentary.
            Ensure the output is complete and do not stop mid-sentence. Finish all 7 sections fully.
            Avoid any repetition or duplicate content across the seven sections. Each item must be unique and not repeated in any other section. 
            """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

tools = [save_tool]
agent = create_tool_calling_agent(
    llm = llm,
    prompt = prompt,
    tools = tools
)

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

agent_runner = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)
raw_response = agent_runner.invoke({"query": query})

try:
    raw_output = raw_response.get("output", "")
    if not raw_output.strip():
        print("Boş çıktı alındı. İşlem yapılmıyor.")
    else:
        previous_raw = load_previous_text()
        if not previous_raw.strip():
            # İlk çalıştırma: tüm çıktıyı olduğu gibi gönder
            send_to_telegram(raw_output, bot_token=telegram_token, chat_id=telegram_chat_id)
            save_current_text(raw_output, "previous_output.txt")
            save_current_text(raw_output + "\n\n---\n\n", "research_output.txt")
            print("İlk çalıştırma: tam çıktı gönderildi ve dosyalar kaydedildi.")
        elif has_new_data(raw_output, previous_raw):
            # Yeni içerik varsa karşılaştır, sadeleştir ve telegrama gönder
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
    print("Error parsing response:", e, "Raw Response -", raw_response)
