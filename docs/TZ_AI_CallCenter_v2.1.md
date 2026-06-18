TEXNIK TOPSHIRIQ
Technical Specification  •  v2.1

AI OVOZLI QO'NG'IROQ MARKAZI AGENTI
Klinikalar uchun AI Receptionist / AI Call-Center yechimi

Hujjat turi
Texnik Topshiriq (TZ)
Versiya
v2.1 — Tuzatilgan va to'ldirilgan
Yo'nalish
Klinika, stomatologiya, diagnostika markazi
Paketlar
Pilot MVP / Standard / Business
Ishlab chiquvchi
____________________
Buyurtmachi
____________________
Sana
____________________

# 1. LOYIHA HAQIDA UMUMIY MA'LUMOT

## 1.1. Loyiha maqsadi
Ushbu loyiha klinikaga kelayotgan telefon qo'ng'iroqlarini avtomatik qabul qiluvchi, bemorlarga kerakli ma'lumotlarni beruvchi, navbatga yozuvchi va zarur holatlarda jonli operatorga ulovchi AI ovozli agentni ishlab chiqishga qaratilgan.

Tizimning asosiy vazifasi — klinika operatorlari yukini kamaytirish, bemorlarga 24/7 rejimida tezkor javob berish, navbat band qilish jarayonini avtomatlashtirish va xizmat sifatini oshirish.

ℹ  AI agent inson operator o'rnini to'liq bosmaydi. U takroriy, standart va xavfsiz suhbatlarni avtomatlashtiradi. Murakkab, tibbiy yoki noaniq holatlarda qo'ng'iroq jonli operatorga uzatiladi.

## 1.2. Asosiy manfaatdor tomonlar
Buyurtmachi
Klinika ma'muriyati
Foydalanuvchilar
Klinikaga qo'ng'iroq qiluvchi bemorlar
Operatorlar
Qo'ng'iroq markazi xodimlari
Adminlar
Tizim va statistikani boshqaruvchi hodimlar
Ishlab chiquvchi
AI yechimlar ishlab chiquvchi tomon

# 2. ASOSIY BIZNES MAQSADLAR

- Klinikaga keladigan oddiy qo'ng'iroqlarning 50–70% qismini AI orqali avtomatik qayta ishlash.
- Operatorlar yukini sezilarli darajada kamaytirish.
- Ish vaqtidan tashqari ham bemor so'rovlarini 24/7 qabul qilish.
- Shifokorlar, xizmatlar, narxlar va ish vaqti bo'yicha tezkor ma'lumot berish.
- Bemorlarni Google Calendar yoki klinika CRM tizimi orqali navbatga yozish.
- Qo'ng'iroqlar tarixi, transkriptlar va statistikani admin panelda ko'rsatish.
- Klinikaga kelayotgan murojaatlarni tahlil qilish va eng ko'p so'raladigan xizmatlarni aniqlash.

# 3. LOYIHA DOIRASI (SCOPE)

## 3.1. Loyiha doirasiga KIRADI
- Kiruvchi telefon qo'ng'iroqlarini AI orqali qabul qilish.
- O'zbek va rus tillarida suhbatlashish.
- Mijoz tilini aniqlash va shu tilda javob berish.
- Klinika haqida ma'lumot berish.
- Xizmatlar va taxminiy narxlar haqida javob berish.
- Shifokorlar jadvali bo'yicha ma'lumot berish.
- Bemorni navbatga yozish.
- Navbatni o'zgartirish yoki bekor qilish so'rovini qabul qilish.
- Jonli operatorga ulash.
- Knowledge Base orqali klinika ma'lumotlarini boshqarish.
- Admin dashboard.
- Qo'ng'iroqlar tarixi va transkriptlar.
- Statistik hisobotlar.
- SMS yoki Telegram orqali eslatma yuborish.
- 1–5 ta parallel qo'ng'iroqni qo'llab-quvvatlash (paketga qarab).
- Production deploy va texnik hujjat topshirish.

## 3.2. Loyiha doirasiga KIRMAYDI
⚠  Quyidagi ishlar ushbu TZ doirasiga kirmaydi va alohida shartnoma asosida kelishiladi.

- Chiquvchi marketing qo'ng'iroqlari.
- Avtomatik sotuv qo'ng'iroqlari.
- Mobil ilova ishlab chiqish.
- To'liq CRM yoki HIS tizimini noldan yaratish.
- 1C integratsiyasi.
- Murakkab tibbiy diagnoz moduli.
- Dori-darmon tavsiya qilish.
- Tibbiy karta bilan chuqur integratsiya.
- Sug'urta tizimlari bilan integratsiya.
- Ko'p filialli murakkab enterprise arxitektura (Business paketida alohida kelishiladi).
- 10+ parallel qo'ng'iroqlar.

# 4. AI AGENT BAJARADIGAN ASOSIY SSENARIYLAR

## 4.1. Klinika haqida ma'lumot
- Klinika manzili va mo'ljal.
- Ish vaqti va dam olish kunlari.
- Telefon raqamlar va filiallar.
- Klinikaga qanday borish mumkinligi.

## 4.2. Xizmatlar va narxlar
- Xizmatlar ro'yxati va taxminiy narxlar.
- Diagnostika xizmatlari va konsultatsiya narxlari.
- Tahlillar haqida umumiy ma'lumot.
- Aksiyalar yoki chegirmalar (klinika tomonidan berilgan bo'lsa).

⚠  AI agent narxni faqat klinika tomonidan tasdiqlab berilgan rasmiy ma'lumotlar asosida aytadi. Narx o'zgargan yoki noaniq bo'lsa, bemor operatorga ulanadi.

## 4.3. Shifokorlar haqida ma'lumot
- Shifokor F.I.O. va mutaxassisligi.
- Qabul vaqtlari va qaysi filialda ishlashi.
- Bo'sh vaqtlar va konsultatsiya narxi.

## 4.4. Navbatga yozish jarayoni
- Bemor qaysi xizmat yoki shifokor kerakligini aytadi.
- AI agent bo'sh vaqtlarni tekshiradi.
- Bemor uchun 2–3 ta vaqt taklif qiladi.
- Bemor vaqtni tanlaydi.
- AI bemorning ismi, telefon raqami va kerakli ma'lumotlarini tasdiqlaydi.
- Navbat Google Calendar yoki CRM tizimiga yoziladi.
- Bemorga SMS yoki Telegram orqali tasdiqlash xabari yuboriladi.

## 4.5. Navbatni o'zgartirish yoki bekor qilish
AI agent bemordan quyidagi ma'lumotlarni so'raydi: ism-familiya, telefon raqam, qaysi shifokorga yozilgani va qabul sanasi. Agar tizim navbatni aniq topsa — o'zgartiradi yoki bekor qiladi. Aniqlik yetarli bo'lmasa, operatorga ulaydi.

## 4.6. Operatorga ulash holatlari
Holat
Tizim harakati
Bemor "operatorga ulang" desa
Darhol uzatadi, 15–30 soniya ichida
Savol tibbiy maslahatga yaqin bo'lsa
Uzatadi, tavsiya bermaydi
Bemor shikoyat bildirsa
Uzatadi, apologiya bilan
AI javobga ishonchi past bo'lsa
Uzatadi, aniq javob bermaydi
Narx yoki jadval noaniq bo'lsa
Uzatadi, operator aniqlashtiradi
Favqulodda holat bo'lsa
103 raqamini aytadi va uzatadi
Bemor g'azablangan bo'lsa
Uzatadi, sakin ohangda
Operator band bo'lsa
Raqamni saqlaydi, qayta qo'ng'iroq vazifasi yaratiladi

# 5. TIBBIY XAVFSIZLIK CHEKLOVLARI

✕  Bu bo'lim o'zgartirilishi yoki chetlab o'tilishi MUMKIN EMAS. Tibbiy xavfsizlik cheklovlari tizimning majburiy tarkibiy qismidir.

## 5.1. AI agent BAJARMAYDIGAN amallar
- Tibbiy diagnoz qo'ymaydi.
- Kasallikni taxmin qilmaydi.
- Dori-darmon tavsiya qilmaydi.
- Dori dozasi haqida maslahat bermaydi.
- Davolanish rejasini tuzmaydi.
- Bemorning shaxsiy tibbiy ma'lumotlarini uchinchi shaxslarga oshkor qilmaydi.
- Boshqa klinika yoki shifokorlar haqida salbiy fikr bildirmaydi.
- Favqulodda holatda suhbatni davom ettirib vaqt yo'qotmaydi.

## 5.2. Favqulodda holat javobi
Favqulodda tibbiy holat aniqlanganda AI agent quyidagi javobni beradi:

✕  "Bu holat shoshilinch tibbiy yordam talab qilishi mumkin. Iltimos, darhol 103 raqamiga qo'ng'iroq qiling yoki eng yaqin shifoxonaga murojaat qiling."

# 6. TIZIM ARXITEKTURASI

## 6.1. Asosiy komponentlar
№
Komponent
Vazifa
Texnologiya
1
Telefoniya
Qo'ng'iroqlarni qabul qilish va uzatish
Twilio / SIP trunk / VoIP
2
STT
Ovozni matnga aylantirish (real-time)
OpenAI Whisper (tavsiya etiladi)
3
LLM
Dialog logikasi va javob generatsiya
Claude API / OpenAI GPT-4o
4
RAG/KB
Klinika ma'lumotlaridan semantik qidiruv
Qdrant + OpenAI Embeddings
5
TTS
Matnni tabiiy ovozga aylantirish
ElevenLabs / OpenAI TTS
6
Orchestration
Barcha jarayonlarni boshqarish
Python FastAPI / Node.js NestJS
7
Admin Panel
Boshqaruv interfeysi
React / Next.js
8
Notification
SMS va Telegram eslatmalar
Eskiz SMS / Play Mobile + TG Bot

## 6.2. Qo'ng'iroq oqimi (Call Flow)
- Qo'ng'iroq virtual raqamga tushadi → Telefoniya qatlami qabul qiladi.
- Salomlashuv matni TTS orqali o'zbek/rus tilida eshittiriladi.
- Bemor gapiradi → STT matnga aylantiradi.
- Matn RAG orqali Knowledge Base'dan mos ma'lumot topadi.
- LLM kontekst + KB ma'lumoti asosida javob yaratadi.
- Javob TTS ovozga aylanadi va bemorga eshittiriladi.
- Navbat so'rovi bo'lsa → Calendar/CRM bilan sinxronlashadi.
- Murakab holat → operator qo'ng'iroqni real-time qabul qiladi.
- Qo'ng'iroq tugagach → transkript, audio va natija saqlanadi.

## 6.3. Infratuzilma
Backend server
VPS yoki cloud, Ubuntu 22.04+, minimum 4 vCPU / 8 GB RAM
Ma'lumotlar bazasi
PostgreSQL (navbatlar, bemorlar, loglar)
Kesh
Redis (sessiya va tez javoblar)
Vector database
Qdrant (Knowledge Base embeddinglar)
Fayl saqlash
AWS S3 yoki Cloudflare R2 (audio yozuvlar)
Deploy
Docker + Docker Compose, CI/CD GitHub Actions
Monitoring
Sentry (xatolar) + Grafana/Prometheus (metrikalar)
SSL
Let's Encrypt, TLS 1.3

# 7. TEXNOLOGIYALAR VA INTEGRATSIYALAR

## 7.1. AI va ovoz texnologiyalari — tavsiya etilgan variantlar

ℹ  Tavsiya etilgan variantlar pilot loyihalar natijasiga asoslanadi. Muqobil variantlar buyurtmachi bilan kelishilgan holda tanlanishi mumkin.

Komponent
Tavsiya etilgan
Muqobil
Izoh
STT
OpenAI Whisper
Deepgram, Yandex SpeechKit
O'zbek va rus tilida eng yaxshi natija
LLM
Claude API (Sonnet)
OpenAI GPT-4o, Gemini
Aniqlik va xavfsizlik uchun
TTS
OpenAI TTS / ElevenLabs
Yandex SpeechKit
Tabiiy ovoz, tezlik
Embedding
OpenAI text-embedding-3-small
Cohere Embed
KB qidiruvi uchun
Vector DB
Qdrant (self-hosted)
Pinecone, pgvector
Narx/sifat balansi

## 7.2. Telefoniya
Asosiy variant
SIP trunk + mahalliy O'zbekiston VoIP provayder
Xalqaro variant
Twilio Programmable Voice
Raqam turi
Klinikaning mavjud raqami (portatsiya) yoki yangi virtual raqam
Eslatma
O'zbekiston raqamlari bilan ishlash uchun mahalliy SIP tanlash tavsiya etiladi

## 7.3. Integratsiyalar
Tizim
Integratsiya turi
Holat
Google Calendar
OAuth 2.0 API v3
Standart paketda kiradi
Telegram Bot
Bot API (xabar va eslatma)
Standart paketda kiradi
Eskiz SMS / Play Mobile
REST API (O'zbekiston SMS)
Standart paketda kiradi
Bitrix24 / AmoCRM
Webhook / REST API
Kelishilgan holda qo'shiladi
Google Sheets
Sheets API v4 (pilot)
Faqat vaqtinchalik pilot uchun
1C / HIS
Alohida integratsiya moduli
TZ doirasidan tashqari

# 8. ADMIN DASHBOARD TALABLARI

## 8.1. Asosiy ko'rinish (Main Dashboard)
- Bugungi qo'ng'iroqlar soni.
- AI orqali hal qilingan qo'ng'iroqlar va foizi.
- Operatorga uzatilgan qo'ng'iroqlar.
- Bugungi navbatlar soni.
- Faol AI agent statusi (online/offline).
- Xatoliklar soni va so'nggi ogohlantirishlar.

## 8.2. Qo'ng'iroqlar tarixi
- Qo'ng'iroq sanasi va vaqti.
- Bemor telefon raqami.
- Suhbat tili (O'zbek/Rus).
- Qo'ng'iroq davomiyligi.
- AI javob bergan yoki operatorga uzatilgan holat.
- To'liq transkript va audio yozuv.
- Qo'ng'iroq natijasi (navbat, ma'lumot, uzatish, bekor).

## 8.3. Navbatlar boshqaruvi
- Yangi, tasdiqlangan, bekor qilingan, o'zgartirilgan navbatlar.
- Shifokor va sana bo'yicha filtrlar.
- Manual o'zgartirish va bekor qilish imkoni.

## 8.4. Knowledge Base boshqaruvi
Admin quyidagi ma'lumotlarni kod yozmasdan boshqara oladi:
- Klinika haqida ma'lumot (manzil, vaqt, kontakt).
- Xizmatlar va narxlar ro'yxati.
- Shifokorlar va filiallar.
- FAQ savol-javoblar.
- Tahlilga tayyorlanish ko'rsatmalari.
- Operatorga ulanish qoidalari.

## 8.5. Foydalanuvchi rollari va huquqlari
Rol
Daraja
Asosiy huquqlar
Super Admin
To'liq kirish
Barcha sozlamalar, xodimlar, billing, integratsiyalar, hisobotlar
Admin
Boshqaruv
Qo'ng'iroqlar, navbatlar, Knowledge Base, statistika
Operator
Cheklangan
O'ziga uzatilgan qo'ng'iroqlar, transkript ko'rish, navbat ko'rish

# 9. PERFORMANCE VA SIFAT TALABLARI

Ko'rsatkich
Talab
Izoh
O'rtacha javob vaqti (latency)
1.5–3.0 soniya
STT+LLM+TTS zanjiri
Maksimal javob vaqti
5 soniyadan oshmasligi
Istisno holatlar bundan mustasno
Parallel qo'ng'iroqlar — Pilot
1–2 ta
MVP bosqichida
Parallel qo'ng'iroqlar — Standard
3–5 ta
Production bosqichida
Parallel qo'ng'iroqlar — Business
5–20 ta
Enterprise arxitektura bilan
Uptime
Kamida 99%
Oylik hisob, texnik ishlar bundan mustasno
O'zbek tili STT aniqligi
Pilot testida baholanadi
Provayderga, muhitga bog'liq
Rus tili STT aniqligi
Kamida 90%
Standart suhbatlarda
Knowledge Base qidiruvi
500 ms ichida
Semantik qidiruv
Operatorga ulash vaqti
15–30 soniya
Operator mavjud bo'lsa

⚠  O'zbek tili STT/TTS sifati provayder, telefon sifati, sheva, shovqin va tibbiy terminlarga bog'liq. Yakuniy aniqlik pilot test natijasiga asoslanadi.

# 10. XAVFSIZLIK TALABLARI

## 10.1. Ma'lumotlar xavfsizligi
- Barcha trafik HTTPS/TLS 1.3 orqali uzatiladi.
- API kalitlar kod ichida saqlanmaydi — environment variables ishlatiladi.
- Ma'lumotlar bazasiga faqat ruxsat berilgan serverlar ulanishi mumkin.
- Admin panel login/parol va 2FA bilan himoyalanadi.
- Har bir admin harakati audit logda saqlanadi.

## 10.2. Shaxsiy ma'lumotlar va saqlash muddati
Ma'lumot turi
Saqlash muddati
Izoh
Audio yozuvlar
30–90 kun
Buyurtmachi bilan kelishiladi
Transkriptlar
90–180 kun
Buyurtmachi bilan kelishiladi
Booking ma'lumotlari
Klinika siyosatiga muvofiq
Odatda 1–3 yil
Loglar
30–90 kun
Xavfsizlik va debug uchun
Audit loglar
Kamida 1 yil
Super Admin harakatlari

ℹ  Qo'ng'iroq boshlanishida bemorga suhbat yozib olinishi mumkinligi haqida ogohlantirish beriladi.

## 10.3. Ma'lumotlar egaligi
✓  Barcha bemor ma'lumotlari, qo'ng'iroq yozuvlari va transkriptlar faqat buyurtmachiga tegishli. Ishlab chiquvchi tomon ushbu ma'lumotlarni uchinchi shaxslarga bermaydi, marketing maqsadlarida ishlatmaydi yoki tizim to'xtatilgandan keyin saqlashda davom etmaydi. Tizim to'xtatilganda barcha ma'lumotlar buyurtmachiga export qilinadi va ishlab chiquvchi serverlaridan o'chiriladi.

# 11. ESLATMA TIZIMI

Vaqt
Kanal
Til
Misol matn
24 soat oldin
SMS + Telegram
O'zbek/Rus
"Ertaga soat 15:00 da dermatolog qabuliga yozilgansiz."
2 soat oldin
SMS
O'zbek/Rus
"Bugun soat 15:00 da qabulingiz bor. Vaqtida keling."
Tasdiqlash (ixtiyoriy)
AI qo'ng'iroq
O'zbek/Rus
"Qabulingizni tasdiqlaysizmi?" — Ha/Yo'q

ℹ  Eslatma kanallari (SMS yoki Telegram) va vaqtlari admin panel orqali sozlanadi.

# 12. LOYIHANI AMALGA OSHIRISH BOSQICHLARI

## 12.1. 1-bosqich — Discovery va tayyorgarlik
Muddat
3–5 ish kuni
Asosiy ishlar
Klinikadan ma'lumotlarni yig'ish, arxitektura tasdiqlash, provayder tanlash
Natija
Yakuniy scope, tasdiqlangan call-flow, integratsiya ro'yxati, test savollar bazasi

## 12.2. 2-bosqich — Pilot MVP
Muddat
3–4 hafta
Asosiy ishlar
Kiruvchi qo'ng'iroq, AI salomlashuv, O'zbek/Rus suhbat, KB javoblar, operatorga ulash, transkript, oddiy admin panel, 1–2 parallel qo'ng'iroq
Natija
Klinikada real test qilishga tayyor pilot agent

## 12.3. 3-bosqich — Standard Production
Muddat
4–8 hafta
Asosiy ishlar
Google Calendar/CRM integratsiyasi, navbat band qilish, SMS/Telegram eslatmalar, to'liq dashboard, KB CRUD, 3–5 parallel qo'ng'iroq, monitoring, load testing, production deploy
Natija
Klinikada ishlatishga tayyor AI call-center tizimi

## 12.4. 4-bosqich — Business/Enterprise (ixtiyoriy)
Muddat
6–12 hafta (alohida kelishiladi)
Asosiy ishlar
Ko'p filialli arxitektura, CRM/HIS integratsiya, 5–20 parallel, outbound qo'ng'iroqlar, chuqur analytics, dedicated server
Natija
Enterprise darajadagi AI call-center platformasi

# 13. QABUL QILISH MEZONLARI

## 13.1. Pilot qabul qilish (Pilot Acceptance)
Test turi
Miqdor
Muvaffaqiyat mezoni
Umumiy test qo'ng'iroqlar
50 ta
Kamida 80% to'g'ri javob
Operatorga uzatish testi
10 ta
Har biri 30 soniya ichida bajariladi
Parallel qo'ng'iroq testi
2 ta bir vaqtda
Ikkalasi ham to'g'ri xizmat ko'rsatadi
O'zbek tili suhbat testi
15 ta
Native nutqchi tomonidan baholanadi
Rus tili suhbat testi
15 ta
Native nutqchi tomonidan baholanadi
Transkript va audio
50 ta
Admin panelda ko'rinadi va yuklanadi
Operator qatnashishi
Kamida 1 nafar
Testda faol ishtirok etadi

## 13.2. Production qabul qilish (Production Acceptance)
Test turi
Miqdor
Muvaffaqiyat mezoni
Umumiy test qo'ng'iroqlar
100 ta
Kamida 85% to'g'ri javob
Booking stsenariylari
30 ta
Hammasi Calendar/CRM'ga yoziladi
Operatorga uzatish
20 ta
Hammasi 30 soniya ichida bajariladi
Noaniq savollar
20 ta
AI to'g'ri operatorga yo'naltiradi
Emergency stsenariylari
10 ta
Hammasi 103 ga yo'naltiradi
"Javob bermaydi" stsenariylari
10 ta
AI hech qanday tibbiy maslahat bermaydi
Parallel qo'ng'iroq testi
3 ta bir vaqtda
Hammasi to'g'ri ishlaydi
SMS/Telegram eslatmalar
10 ta
Vaqtida va to'g'ri yuboriladi
O'rtacha javob vaqti
Barchasi
3 soniyadan oshmasligi kerak

## 13.3. Qabul qilishdan bosh tortish holati
⚠  Agar test natijalari belgilangan mezonlarga to'g'ri kelmasa, ishlab chiquvchi 10 ish kuni ichida kamchiliklar bartaraf etib, qayta test o'tkazadi. Ikkinchi testdan keyin ham mezon bajarilmasa, buyurtmachi to'langan summasining 50% ini qaytarib olish huquqiga ega.

# 14. NARX VA TO'LOV MODELI

ℹ  Barcha narxlar AQSh dollari (USD) da ko'rsatilgan. Oylik xarajatlar (API, hosting, telefoniya) ishlatilish hajmiga qarab o'zgarishi mumkin.

## 14.1. Paketlar va bir martalik ishlab chiqish narxi
Tarkib
Pilot MVP
Standard
Business
Narx (bir martalik)
$2,000 – $3,000
$4,500 – $7,000
$8,000 – $15,000+
Kiruvchi qo'ng'iroq + AI agent
✓
✓
✓
O'zbek + Rus tili
✓
✓
✓
Knowledge Base (asosiy)
✓
✓ (RAG)
✓ (RAG+)
Operatorga ulash
✓
✓
✓
Qo'ng'iroq transkripti
✓
✓
✓
Admin panel
Asosiy
To'liq
Enterprise
Google Calendar integratsiya
—
✓
✓
SMS/Telegram eslatmalar
—
✓
✓
Parallel qo'ng'iroqlar
1–2 ta
3–5 ta
5–20 ta
Monitoring va error tracking
—
✓
✓
Ko'p filialli arxitektura
—
—
✓
CRM/HIS integratsiya
—
—
✓
Outbound eslatma qo'ng'iroqlari
—
—
✓
Chuqur analytics
—
—
✓
Dedicated server
—
—
✓
SLA kafolati
—
—
✓

## 14.2. Oylik platform xarajatlari (Service Fee)
Xizmat tarkibi
Pilot
Standard
Business
Platform service fee
$100–200/oy
$200–400/oy
$400–800/oy
Server monitoring
✓
✓
✓
Xatoliklarni kuzatish
✓
✓
✓
Minor bug fix
✓
✓
✓
KB texnik qo'llab-quvvatlash
✓
✓
✓
Backup nazorati
✓
✓
✓
Priority support (ish kunlari)
—
✓
✓
24/7 kritik support
—
—
✓

## 14.3. Usage-based xarajatlar (API va telefoniya)
AI qo'ng'iroq xarajatlari ishlatilgan minutga qarab hisoblanadi:

Xarajat turi
Taxminiy narx
Izoh
LLM (Claude/OpenAI)
$0.03–0.08/min
Token hajmiga qarab
STT (Whisper/Deepgram)
$0.02–0.05/min
Provaydерga qarab
TTS (ElevenLabs/OpenAI)
$0.02–0.06/min
Provaydерga qarab
Telefoniya (Twilio/SIP)
$0.02–0.08/min
Raqam va trafikka qarab
SMS eslatma
$0.01–0.03/SMS
O'zbekiston raqamlari
JAMI (taxminiy)
$0.09–0.27/min
Optimallashtirilgan holda

✓  Misol: Klinika oyiga 3,000 daqiqa qo'ng'iroq ishlatsa: 3,000 × $0.15 = $450 usage + $300 service fee = Jami ~$750/oy

## 14.4. API narxlari o'zgarishi hollati
⚠  Uchinchi tomon API provayderlari (OpenAI, ElevenLabs, Twilio va boshqalar) narxlarini o'zgartirganda, buyurtmachi kamida 14 kalendar kun oldin yozma ravishda xabardor qilinadi. Narx 20% dan ortiq oshsa, buyurtmachi shartnomani 30 kunlik ogohlantirish bilan faqat usage-based qismiga nisbatan qayta ko'rib chiqish huquqiga ega.

# 15. TO'LOV SHARTLARI

## 15.1. Pilot MVP uchun to'lov jadvali
Bosqich
Foiz
To'lov sharti
1-to'lov
50%
Shartnoma imzolanganda, ish boshlanishida
2-to'lov
30%
Birinchi demo taqdimoti muvaffaqiyatli bo'lganda
3-to'lov
20%
Pilot to'liq topshirilganda va qabul qilinganida

## 15.2. Standard va Business uchun to'lov jadvali
Bosqich
Foiz
To'lov sharti
1-to'lov
30%
Shartnoma imzolanganda
2-to'lov
40%
Beta versiya tayyor bo'lganda va demo o'tkazilganda
3-to'lov
30%
Loyiha to'liq topshirilganda va yozma qabul qilinganida

ℹ  Uchinchi tomon xarajatlari (API, hosting, telefoniya, SMS) buyurtmachi tomonidan alohida qoplanadi yoki xizmat ko'rsatuvchi orqali 10–15% servis haqi bilan yuritiladi. Bu kelishiladi.

# 16. KAFOLAT VA TEXNIK QO'LLAB-QUVVATLASH

## 16.1. Kafolat muddati
Paket
Kafolat muddati
Tarkibi
Pilot MVP
60 kun
Ishlab chiqish bilan bog'liq xatoliklar bepul tuzatiladi
Standard
60 kun
Ishlab chiqish bilan bog'liq xatoliklar bepul tuzatiladi
Business
90 kun
Ishlab chiqish bilan bog'liq xatoliklar + prioritet qo'llab-quvvatlash

⚠  Kafolat quyidagilarni qamrab OLMAYDI: yangi funksiyalar, scope'dan tashqari o'zgarishlar, uchinchi tomon API muammolari, buyurtmachi tomonidan noto'g'ri o'zgartirilgan sozlamalar, telefoniya yoki internet provayder muammolari.

## 16.2. Texnik yordam darajalari
Daraja
Javob vaqti
Ish vaqti
Kanal
Kritik xatolik (tizim ishlamaydi)
4 soat ichida
24/7 (Business), ish kunlari (boshqalar)
Telegram/Telefon
Yuqori ustuvorlik
8 soat ichida
Ish kunlari 09:00–18:00
Telegram/Email
Oddiy xatolik
1–2 ish kuni
Ish kunlari 09:00–18:00
Telegram/Email
So'rov/taklif
3–5 ish kuni
Ish kunlari
Email

# 17. RISKLAR VA CHEKLOVLAR

Risk
Darajasi
Yumshatish chorasi
O'zbek tili STT sifati past bo'lishi
O'rta
Pilot testida baholanadi, muqobil provayder tayyorlanadi
Telefoniya provider sifati latencyga ta'sir
O'rta
Mahalliy SIP provayder bilan ishlash, test o'tkazish
Klinikadan ma'lumotlar noto'liq yoki kech kelishi
Yuqori
Buyurtmachi ma'lumot checklist bilan bog'lanadi, kechikish muddat uzayishiga olib keladi
Tibbiy xavfsizlik risklar
Kritik
Tibbiy cheklovlar kodga hard-coded, prompt injectiondan himoya
API narxlari o'zgarishi
Past
14 kun oldin ogohlantirish, narx o'zgarsa shartnomani ko'rib chiqish huquqi
CRM integratsiyasi ochiq API yo'qligi
O'rta
Discovery bosqichida API mavjudligi tekshiriladi
Parallel qo'ng'iroqlar soni ortib ketishi
Past
Auto-scaling arxitektura, yuqori paketga o'tish taklifi

# 18. BUYURTMACHIDAN TALAB QILINADIGAN MA'LUMOTLAR

⚠  Buyurtmachi ushbu ma'lumotlarni Discovery bosqichida taqdim etishi shart. Ma'lumotlar kechiksa, loyiha muddati mos ravishda uzaytiriladi.

№
Ma'lumot turi
Format
Muddat
1
Klinika nomi, manzil, ish vaqti, kontaktlar
Matn / Excel
Discovery 1-kuni
2
Filiallar ro'yxati (agar mavjud)
Matn / Excel
Discovery 1-kuni
3
Shifokorlar ro'yxati (FIO, mutaxassislik)
Excel
Discovery 2-kuni
4
Shifokorlar ish jadvali
Excel / Google Calendar
Discovery 2-kuni
5
Xizmatlar va taxminiy narxlar
Excel / PDF
Discovery 2-kuni
6
FAQ savol-javoblar (kamida 30 ta)
Matn / Excel
Discovery 3-kuni
7
Operatorlar ro'yxati va kontaktlari
Excel
Discovery 3-kuni
8
Google Calendar / CRM kirish ruxsati
OAuth / API key
Discovery 4-kuni
9
SMS provider ma'lumotlari (Eskiz/PlayMobile)
API key
Discovery 4-kuni
10
Telefoniya provider (SIP/Twilio) ma'lumotlari
SIP credentials
Discovery 4-kuni
11
Asosiy suhbat ssenariylari
Matn
Discovery 3-kuni
12
Rasmiy tibbiy cheklovlar va javob siyosati
PDF / Matn
Discovery 2-kuni

# 19. LOYIHA YAKUNIDA TOPSHIRILADIGAN NARSALAR

Topshiriladigan narsa
Standard
Business
Ishlaydigan AI voice agent (production)
✓
✓
Admin dashboard va operator panel
✓
✓
Knowledge Base boshqaruv paneli
✓
✓
Google Calendar / CRM booking integratsiya
✓
✓
SMS va Telegram eslatma tizimi
✓
✓
Qo'ng'iroqlar tarixi va transkriptlar
✓
✓
Monitoring va error tracking sozlangan
✓
✓
Texnik arxitektura hujjati
✓
✓
Admin va operator uchun qo'llanma
✓
✓
Ma'lumotlar export funksiyasi
✓
✓
60 kunlik bepul bug-fix kafolati
✓
✓ (90 kun)
Ko'p filialli arxitektura
—
✓
Outbound qo'ng'iroq moduli
—
✓
Dedicated server sozlamalari
—
✓
SLA hujjati
—
✓

# 20. IMZO VA TASDIQLASH

Ushbu Texnik Topshiriq ikki tomon tomonidan o'qilgan, tushunilgan va kelishilgan hisoblanadi. Imzo qo'yilgandan so'ng hujjat yuridik kuchga ega bo'ladi.

ISHLAB CHIQUVCHI
BUYURTMACHI
Tashkilot nomi: ____________________
Klinika nomi: ____________________
Vakil (FIO): ____________________
Vakil (FIO): ____________________
Lavozim: ____________________
Lavozim: ____________________
Imzo: ____________________
Imzo: ____________________
Sana: ____________________
Sana: ____________________
M.O.'
M.O.'
