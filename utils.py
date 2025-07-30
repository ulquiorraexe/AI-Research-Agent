import textwrap
import os
import requests

def load_previous_text(filepath="previous_output.txt"):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def save_current_text(text, filepath="previous_output.txt"):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

def has_new_data(new_text: str, old_text: str) -> bool:
    new_clean = " ".join(new_text.split())
    old_clean = " ".join(old_text.split())
    return new_clean != old_clean

def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )

def split_message(message: str, max_length: int = 3500) -> list[str]:
    parts = []
    while len(message) > max_length:
        split_at = message.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        parts.append(message[:split_at])
        message = message[split_at:].lstrip()
    parts.append(message)
    return parts

def send_to_telegram(message: str, bot_token: str, chat_id: str) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    success = True

    try:
        safe_message = escape_html(message)
        chunks = split_message(safe_message, max_length=3500)

        for i, chunk in enumerate(chunks):
            payload = {
                "chat_id": chat_id,
                "text": chunk.strip(),
                "parse_mode": "HTML",
            }
            response = requests.post(url, data=payload)
            if not response.ok:
                print(f"Chunk {i+1} gönderilirken Telegram API hatası: {response.status_code} - {response.text}")
                success = False
            else:
                print(f"Chunk {i+1} başarıyla gönderildi. ({len(chunk)} karakter)")
        return success

    except Exception as e:
        print(f"Telegram mesaj gönderirken genel hata oluştu: {e}")
        return False