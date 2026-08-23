"""
tashkent.hh.uz saytidagi Data Analyst / Data Scientist / Data Engineer /
BI Developer / Business Analyst va shunga o'xshash bo'sh ish o'rinlarini
kuzatib boruvchi bot.

Ishlash tartibi:
1. HeadHunter (hh.ru / hh.uz) ochiq API'si orqali berilgan hudud (Toshkent)
   bo'yicha vakansiyalar ro'yxatini oladi.
2. Vakansiya nomi (name) ichida KEYWORDS ro'yxatidagi so'zlardan biri
   uchrasa, uni "mos" deb hisoblaydi.
3. Oldin yuborilgan vakansiyalar seen_vacancies.json faylida saqlanadi,
   shu bois faqat YANGI vakansiyalar Telegram kanaliga yuboriladi.

Bot GitHub Actions orqali har 5 daqiqada avtomatik ishga tushiriladi
(.github/workflows/monitor.yml faylga qarang).
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# SOZLAMALAR
# ---------------------------------------------------------------------------

# Qidiruvda ishlatiladigan kalit so'zlar (katta-kichik harflarga sezgir emas)
KEYWORDS = [
    "analitik", "стажер",
    "analyst", "analytic",
    "аналитик", "аналист",
    "data", "дата",
]

# hh API'dagi hudud kodi: 2759 = Toshkent shahri, 97 = butun O'zbekiston.
# GitHub repo -> Settings -> Secrets and variables -> Actions -> Variables
# bo'limida HH_AREA_ID nomli o'zgaruvchi qo'shib, buni qayta sozlash mumkin.
AREA_ID = os.environ.get("HH_AREA_ID") or "2759"

# Natijalarni hh.uz saytiga tegishli qilib olish uchun
HH_HOST = "hh.uz"

HH_API_URL = "https://api.hh.ru/vacancies"
PER_PAGE = 100
MAX_PAGES = 10  # ortiqcha so'rov yubormaslik uchun cheklov

SEEN_FILE = Path(__file__).parent / "seen_vacancies.json"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("hh_monitor")


# ---------------------------------------------------------------------------
# YORDAMCHI FUNKSIYALAR
# ---------------------------------------------------------------------------

def load_seen_ids() -> set:
    if SEEN_FILE.exists():
        try:
            data = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
            return set(data.get("seen_ids", []))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("seen_vacancies.json o'qishda xatolik: %s", exc)
    return set()


def save_seen_ids(seen_ids: set) -> None:
    # Fayl cheksiz o'smasligi uchun oxirgi 5000 ta ID saqlanadi
    trimmed = list(seen_ids)[-5000:]
    SEEN_FILE.write_text(
        json.dumps({"seen_ids": trimmed}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def matches_keywords(title: str) -> bool:
    title_lower = title.lower()
    return any(keyword.lower() in title_lower for keyword in KEYWORDS)


def fetch_vacancies() -> list:
    """hh API orqali barcha sahifalardagi mos vakansiyalarni yig'ib qaytaradi."""
    all_items = []
    headers = {
        # hh API tavsiyasiga ko'ra tavsifli User-Agent yuborish tavsiya etiladi
        "User-Agent": "tashkent-hh-data-jobs-bot/1.0 (+https://github.com/)",
        "Accept": "application/json",
        "Accept-Language": "ru,uz;q=0.9,en;q=0.8",
    }
    query = " OR ".join(KEYWORDS)

    for page in range(MAX_PAGES):
        params = {
            "text": query,
            "search_field": "name",
            "area": AREA_ID,
            "host": HH_HOST,
            "per_page": PER_PAGE,
            "page": page,
            "order_by": "publication_time",
        }
        try:
            resp = requests.get(HH_API_URL, params=params, headers=headers, timeout=20)
            resp.raise_for_status()
        except requests.HTTPError as exc:
            body_snippet = ""
            server_header = ""
            if exc.response is not None:
                body_snippet = exc.response.text[:500]
                server_header = exc.response.headers.get("Server", "noma'lum")
            log.error(
                "hh API xato qaytardi: %s | Server: %s | Javob tanasi: %s",
                exc, server_header, body_snippet,
            )
            break
        except requests.RequestException as exc:
            log.error("hh API'ga so'rov yuborishda xatolik: %s", exc)
            break

        data = resp.json()
        items = data.get("items", [])
        all_items.extend(items)

        total_pages = data.get("pages", 1)
        if page >= total_pages - 1:
            break
        time.sleep(0.3)  # API'ga hurmat yuzasidan kichik pauza

    return all_items


def format_message(vacancy: dict) -> str:
    name = vacancy.get("name", "Noma'lum lavozim")
    employer = (vacancy.get("employer") or {}).get("name", "Noma'lum kompaniya")
    area = (vacancy.get("area") or {}).get("name", "")
    url = vacancy.get("alternate_url", "")

    salary_text = "Ko'rsatilmagan"
    salary = vacancy.get("salary")
    if salary:
        s_from = salary.get("from")
        s_to = salary.get("to")
        currency = salary.get("currency", "")
        if s_from and s_to:
            salary_text = f"{s_from:,} - {s_to:,} {currency}"
        elif s_from:
            salary_text = f"{s_from:,}+ {currency}"
        elif s_to:
            salary_text = f"{s_to:,} gacha {currency}"

    return (
        f"🆕 <b>{name}</b>\n"
        f"🏢 {employer}\n"
        f"📍 {area}\n"
        f"💰 {salary_text}\n"
        f"🔗 <a href=\"{url}\">Vakansiyani ko'rish</a>"
    )


def send_telegram_message(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.error("TELEGRAM_BOT_TOKEN yoki TELEGRAM_CHAT_ID sozlanmagan.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        log.error("Telegramga xabar yuborishda xatolik: %s", exc)
        return False


# ---------------------------------------------------------------------------
# ASOSIY OQIM
# ---------------------------------------------------------------------------

def main() -> int:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.error(
            "TELEGRAM_BOT_TOKEN va TELEGRAM_CHAT_ID muhit o'zgaruvchilari "
            "sozlanmagan. Ularni GitHub repo -> Settings -> Secrets and "
            "variables -> Actions bo'limiga qo'shing."
        )
        return 1

    seen_ids = load_seen_ids()
    log.info("Hozircha ko'rilgan vakansiyalar soni: %d", len(seen_ids))

    vacancies = fetch_vacancies()
    log.info("hh API'dan qidiruv natijasi: %d ta vakansiya", len(vacancies))

    new_count = 0
    for vacancy in vacancies:
        vid = vacancy.get("id")
        name = vacancy.get("name", "")

        if vid in seen_ids:
            continue
        if not matches_keywords(name):
            continue

        message = format_message(vacancy)
        if send_telegram_message(message):
            seen_ids.add(vid)
            new_count += 1
            log.info("Yuborildi: %s", name)
            time.sleep(1)  # Telegram rate-limit uchun kichik pauza
        else:
            log.warning("Yuborilmadi (keyingi safar qayta urinib ko'riladi): %s", name)

    save_seen_ids(seen_ids)
    log.info("Tugadi. Jami %d ta yangi vakansiya yuborildi.", new_count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
