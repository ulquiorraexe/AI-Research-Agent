import textwrap
import os
import requests
import re
from difflib import unified_diff
import difflib
from datetime import date

def is_similar(text1: str, text2: str, threshold: float = 0.92) -> bool:
    """İki metin ne kadar benzer? %92 ve üzeri benzerse 'aynı' say."""
    ratio = difflib.SequenceMatcher(None, text1.strip(), text2.strip()).ratio()
    return ratio >= threshold

def append_to_text_file(text, filepath="research_output.txt"):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(text + "\n\n" + "="*80 + "\n\n")

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

def split_into_categories(text: str) -> list[str]:
    # "1)", "2)", ... "7)" başlıklarına göre böl
    pattern = re.compile(r"(?=\d\))")
    parts = pattern.split(text)
    return [p.strip() for p in parts if p.strip()]

def compare_categories(new_cats: list[str], old_cats: list[str]) -> list[str]:
    max_len = max(len(new_cats), len(old_cats))
    result = []
    for i in range(max_len):
        new_cat = new_cats[i] if i < len(new_cats) else ""
        old_cat = old_cats[i] if i < len(old_cats) else ""

        if not new_cat:
            result.append("Bugün bu kategoride yeni bir gelişme yok.")
            continue

        if is_similar(new_cat, old_cat):
            lines = new_cat.splitlines()
            if lines:
                header = lines[0]
                replaced = header + "\nBugün bu kategoride yeni bir gelişme yok."
                result.append(replaced)
            else:
                result.append("Bugün bu kategoride yeni bir gelişme yok.")
        else:
            result.append(new_cat)
    return result

def compare_and_prepare_output(new_output: str, previous_filepath="previous_output.txt", research_filepath="research_output.txt") -> str:
    old_output = load_previous_text(previous_filepath)
    new_cats = split_into_categories(new_output)
    old_cats = split_into_categories(old_output)

    compared = compare_categories(new_cats, old_cats)
    final_text = "\n\n".join(compared)

    # research_output.txt'ye ekle
    append_to_text_file(final_text, research_filepath)

    # previous_output.txt'yi yeni çıktı ile güncelle
    save_current_text(new_output, previous_filepath)

    return final_text

def prepare_and_send_message(new_output: str, bot_token: str, chat_id: str) -> bool:
    try:
        previous_output = load_previous_text()

        # Farkları bul (satır satır)
        previous_lines = previous_output.splitlines(keepends=True)
        new_lines = new_output.splitlines(keepends=True)
        diff = unified_diff(previous_lines, new_lines, lineterm='')

        # Farklı satırları al
        diff_lines = [line for line in diff if line.startswith('+ ') and not line.startswith('+++')]

        if not diff_lines:
            return False  # Gerçek bir fark yok

        today = date.today().isoformat()
        message = f"📌 {today} - Güncelleme:\n\n" + ''.join(diff_lines)

        # Telegram'a gönder
        send_to_telegram(message, bot_token, chat_id)

        # Güncel veriyi iki dosyaya yaz
        save_current_text(new_output, "previous_output.txt")
        save_current_text(f"--- {today} ---\n{new_output}\n\n", "research_output.txt")

        return True

    except Exception as e:
        print("prepare_and_send_message error:", e)
        return False