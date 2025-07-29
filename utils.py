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


def send_to_telegram(message: str, bot_token: str, chat_id: str, chunk_size=3900) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    success = True  # Her parçanın başarılı olup olmadığını takip et
    try:
        lines = message.splitlines()
        chunk = ""

        for line in lines:
            if len(chunk) + len(line) + 1 < chunk_size:
                chunk += line + "\n"
            else:
                payload = {
                    "chat_id": chat_id,
                    "text": chunk.strip(),
                    "parse_mode": "HTML",
                }
                response = requests.post(url, data=payload)
                if not response.ok:
                    print(f"Telegram API hatası: {response.status_code} - {response.text}")
                    success = False  # Ama diğer chunk'lara devam et
                chunk = line + "\n"

        if chunk.strip():
            payload = {
                "chat_id": chat_id,
                "text": chunk.strip(),
                "parse_mode": "HTML",
            }
            response = requests.post(url, data=payload)
            if not response.ok:
                print(f"Telegram API hatası: {response.status_code} - {response.text}")
                success = False

        return success

    except Exception as e:
        print(f"Telegram mesaj gönderirken hata oluştu: {e}")
        return False