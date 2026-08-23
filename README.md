# HH.uz Data Vakansiyalar Monitoringi (Telegram bot)

Bu bot `hh.uz` (Toshkent) saytidagi Data Analyst, Data Scientist, Data
Engineer, BI Developer, Business Analyst va shunga o'xshash vakansiyalarni
kuzatib boradi va **yangi** e'lonlarni Telegram kanaliga avtomatik yuboradi.

Bot hh.ru/hh.uz'ning rasmiy ochiq API'sidan foydalanadi (sahifani "scrape"
qilmaydi), shuning uchun barqaror ishlaydi. Ishga tushirish GitHub Actions
orqali amalga oshiriladi — har 5 daqiqada avtomatik tekshiradi, hech qanday
serverga ehtiyoj yo'q.

## Fayllar

- `hh_monitor.py` — asosiy skript: hh API'dan vakansiyalarni oladi, kalit
  so'zlar bo'yicha filtrlaydi va yangilarini Telegramga yuboradi.
- `seen_vacancies.json` — allaqachon yuborilgan vakansiyalar ID'lari
  saqlanadigan fayl (takroriy xabar yuborilmasligi uchun).
- `.github/workflows/monitor.yml` — GitHub Actions workflow, har 5 daqiqada
  botni ishga tushiradi va `seen_vacancies.json`ni repo'ga qaytarib commit
  qiladi.
- `requirements.txt` — kerakli Python kutubxonalari.

## Qidirilayotgan kalit so'zlar

```
analitik, стажер, analyst, analytic, аналитик, аналист, data, дата
```

Vakansiya nomida (title) shu so'zlardan biri katta-kichik harflarga
qaramasdan uchrasa — bot uni Telegramga yuboradi. Ro'yxatni o'zgartirish
uchun `hh_monitor.py` faylidagi `KEYWORDS` ro'yxatini tahrirlang.

## O'rnatish (bosqichma-bosqich)

### 1. Telegram bot yaratish

1. Telegram'da [@BotFather](https://t.me/BotFather)ga o'ting.
2. `/newbot` buyrug'ini yuboring va ko'rsatmalarga amal qiling.
3. Sizga beriladigan **token**ni saqlab qo'ying (masalan:
   `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).

### 2. Telegram kanal tayyorlash

1. Yangi Telegram kanal yarating (yoki mavjudini ishlating).
2. Botingizni kanalga **administrator** sifatida qo'shing (kamida "Post
   messages" huquqi bilan).
3. Kanal `chat_id`sini aniqlang:
   - Agar kanal ochiq (public) bo'lsa va username'i bo'lsa — shunchaki
     `@kanal_username` dan foydalanish mumkin.
   - Agar kanal yopiq (private) bo'lsa — kanalga bitta xabar yuboring,
     so'ng o'sha xabarni [@JsonDumpBot](https://t.me/JsonDumpBot)ga forward
     qiling, u sizga `chat.id` qiymatini beradi (odatda `-100` bilan
     boshlanadigan raqam).

### 3. GitHub reponi tayyorlash

1. Ushbu papkadagi barcha fayllarni yangi GitHub repo'ga yuklang (yoki
   mavjud repo'ga qo'shing).
2. Repo -> **Settings -> Actions -> General -> Workflow permissions**
   bo'limiga o'ting va **"Read and write permissions"**ni tanlang, so'ng
   saqlang. (Bu — botga `seen_vacancies.json` faylini avtomatik commit
   qilishga ruxsat beradi.)
3. Repo -> **Settings -> Secrets and variables -> Actions -> Secrets**
   bo'limida quyidagi ikkita **secret** qo'shing:
   - `TELEGRAM_BOT_TOKEN` — 1-bosqichda olingan token.
   - `TELEGRAM_CHAT_ID` — 2-bosqichda aniqlangan chat_id yoki
     `@kanal_username`.
4. (Ixtiyoriy) Xuddi shu bo'limdagi **Variables** yorlig'ida `HH_AREA_ID`
   nomli o'zgaruvchi qo'shishingiz mumkin:
   - `2759` — faqat Toshkent shahri (standart qiymat).
   - `97` — butun O'zbekiston bo'yicha (Toshkentdan tashqari viloyatlar
     ham).

### 4. Ishga tushirish

Workflow avtomatik ravishda har 5 daqiqada ishga tushadi (`cron: "*/5 * * *
*"`). Birinchi marta qo'lda tekshirib ko'rish uchun: repo -> **Actions**
bo'limi -> "HH.uz Data Jobs Monitor" -> **Run workflow** tugmasini bosing.

## Muhim eslatmalar

- GitHub Actions'ning `schedule` (cron) triggerlari **aniq vaqtda emas**,
  balki GitHub navbatiga qarab bir necha daqiqa kechikishi mumkin — bu
  GitHub'ning umumiy cheklovi, botga bog'liq emas.
- hh API rasmiy hujjatlariga ko'ra so'rovlar soni cheklangan (rate limit).
  Har 5 daqiqada bitta so'rov yuborish bu chegaradan ancha past, shuning
  uchun muammo bo'lmaydi.
- Botni faqat bitta kanalga emas, bir nechta joyga yubormoqchi bo'lsangiz,
  `send_telegram_message` funksiyasini bir nechta `chat_id` bo'yicha
  aylanadigan qilib o'zgartirishingiz mumkin.
