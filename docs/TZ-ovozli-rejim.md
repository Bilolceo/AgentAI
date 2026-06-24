# Texnik Topshiriq (TZ): Real Ovozli AI Registrator

Hujjat versiyasi: 1.0
Sana: 2026-06-24
Loyiha: Urologiya klinikasi uchun AI ovozli call-center agent
Maqsad hujjati: matnli simulyatsiyadan **real telefon qo'ng'iroqlariga** o'tish

> Eslatma: Loyihaning umumiy TZ'si `docs/TZ_AI_CallCenter_v2.1.md` da. Ushbu
> hujjat faqat **real ovozli rejimni ishga tushirish** bo'yicha aniq topshiriq.

---

## 1. Maqsad

Klinikaga kelgan telefon qo'ng'irog'iga AI agent o'zbek/rus tilida javob beradi,
klinika haqida ma'lumot beradi, qabulga yozadi, murakkab/xavfli holatlarda
operatorga uzatadi. Qo'ng'iroq transkripti va audio yozuvi saqlanadi, admin
paneldа ko'rinadi.

## 2. Hozirgi holat (boshlang'ich nuqta)

Quyidagilar **allaqachon mavjud** (kod + testlar bilan):
- Backend (FastAPI), 553+ test, mock-first provider arxitekturasi
- Ovoz qatlami kodi: Deepgram STT/TTS adapterlari, Twilio Media Streams (WebSocket
  audio), `pipeline`, `live_call`, `readiness`, `recordings`, latency metrikalari
- Tibbiy xavfsizlik (diagnoz/dori taqiqi, 103 favqulodda), operatorga uzatish
- Qabul tizimi (shifokor, slot, booking) + onlayn yozilish + SMS tasdiq (mock)
- Admin / rahbar / mijoz panellari, Railway'da deploy

**Yetishmaydigan / faollashtirilishi kerak:**
- Real telefon raqami (SIP/Twilio) ulanmagan
- Real STT/TTS provider kalitlari yo'q (hozir mock)
- Real klinika ma'lumotlari (manzil, narx, shifokorlar, FAQ) kiritilmagan
- Real qo'ng'iroqларда sifat/latency sinovdan o'tmagan

## 3. Qamrov (Scope)

### 3.1 Kiradi (ushbu TZ)
- Bitta klinika raqamiga kiruvchi qo'ng'iroqlar
- O'zbek va rus tili (avtoaniqlash)
- Salomlashish, klinika ma'lumoti, qabulga yozish, operatorga uzatish, favqulodda
- Transkript + audio yozuv saqlash, admin panelда ko'rsatish
- 50 ta real test qo'ng'irog'i bilan pilot

### 3.2 Kirmaydi (keyingi bosqich)
- Chiquvchi (outbound) qo'ng'iroqlar, marketing obzvonlar
- Bir nechta filial/raqam, IVR menyu daraxti
- To'lov, CRM/Google Calendar to'liq integratsiyasi
- Telegram/WhatsApp ovozli xabar

## 4. Arxitektura va ma'lumot oqimi

```
Mijoz qo'ng'iroq qiladi
  -> Telefon raqam (SIP-trunk / Twilio) 
  -> Webhook: kiruvchi qo'ng'iroq (TwiML <Connect><Stream>)
  -> WebSocket Media Stream (real-time audio, base64 ulaw)
       -> STT (nutq -> matn, uz/ru streaming)
       -> AI agent (Claude): system prompt + tool-use
            -> RAG / bilim bazasi (klinika ma'lumoti)
            -> Booking (slot tekshirish, qabulga yozish)
            -> Safety guard (diagnoz/dori taqiqi, favqulodda)
            -> Operator transfer (shartlar bo'yicha)
       -> TTS (matn -> nutq, uz/ru) -> mijozga ovoz
  -> Qo'ng'iroq tugaydi
       -> Transkript + audio yozuv saqlanadi
       -> SMS tasdiq (agar qabulga yozilgan bo'lsa)
       -> Admin panelда ko'rinadi
```

## 5. Provider tanlovlari (qaror talab qiladigan)

| Qatlam | Tavsiya | Sabab / izoh |
|---|---|---|
| Telefon raqam | Lokal SIP-trunk (yoki Twilio number) | UZ uchun lokal raqam tabiiy; Twilio UZ raqam sotmaydi |
| Telefoniya transport | Twilio Voice + Media Streams | Kodда tayyor; SIP-ni Twilio'ga ulasa bo'ladi |
| STT (nutq->matn) | Deepgram (kodда bor) yoki Azure Speech | O'zbek sifatини REAL audioда test qilish shart |
| TTS (matn->nutq) | Deepgram yoki Azure (uz-UZ neural) | Azure'да uz-UZ ovozlar bor; sifat solishtiriladi |
| LLM (suhbat) | Claude (Sonnet/Haiku) | Past latency, tool-use; kodда provider bor |

> Asosiy risk: **o'zbek nutqini telefon sifatида aniq tanish (STT)**. Bu eng katta
> noaniqlik — pilotning birinchi ishi shuni o'lchash.

## 6. Funksional talablar

### 6.1 Salomlashish va til
- F-1: Qo'ng'iroq boshlanganda AI tabriklaydi (uz default), masalan: "Assalomu
  alaykum, [klinika] registraturasi. Sizga qanday yordam bera olaman?"
- F-2: Mijoz tilini (uz/ru) aniqlab, o'sha tilда davom etadi
- F-3: Tushunmaган joyда qayta so'raydi ("Uzr, qaytaring iltimos")

### 6.2 Klinika ma'lumoti
- F-4: Manzil, ish vaqti, telefon, yo'nalishlar haqida javob (bilim bazasidan)
- F-5: Xizmat va narxlar; narx noaniq bo'lsa — operatorga uzatadi
- F-6: Shifokorlar (FIO, mutaxassislik, qabul kunlari)

### 6.3 Qabulga yozish (ovoz orqali)
- F-7: Bo'sh vaqtlarni tekshiradi, 2-3 variant taklif qiladi
- F-8: Ism va telefonni tasdiqlaydi
- F-9: Qabulni yozadi (mavjud booking tizimi orqali, status pending)
- F-10: Tasdiq SMS yuboriladi (mavjud SMS moduli)
- F-11: Qabulni o'zgartirish/bekor qilish (Standard — ixtiyoriy)

### 6.4 Operatorga uzatish
- F-12: Quyidagi hollarда operatorga uzatadi yoki callback yozadi:
  mijoz "operator" so'rasa, shikoyat, jahl, AI ishonchsiz, narx/jadval noaniq,
  operator band bo'lsa -> qayta qo'ng'iroq topshirig'i

### 6.5 Tibbiy xavfsizlik (KRITIK)
- F-13: AI diagnoz qo'ymaydi, dori/doza tavsiya qilmaydi, davolash rejasi tuzmaydi
- F-14: Favqulodda belgilarда aniq matn: "...darhol 103 ga qo'ng'iroq qiling..."
- F-15: Bemor ma'lumotini uchinchi shaxsga oshkor qilmaydi
- F-16: Boshqa klinika/shifokor haqida salbiy gapirmaydi

### 6.6 Yozib olish va ko'rsatish
- F-17: Har bir qo'ng'iroq transkripti saqlanadi (uz/ru)
- F-18: Audio yozuv saqlanadi (xavfsiz storage)
- F-19: Admin panelда qo'ng'iroqlar ro'yxati, transkript, audio yuklab olish
- F-20: Telefon raqamlari panelда niqoblanadi (maskalanadi)

## 7. Nofunksional talablar

- NF-1: Javob latency (mijoz gapirib bo'lgach AI ovozi boshlanishi) maqsad
  < 1.5 soniya (real-time his qilinishi uchun)
- NF-2: Barge-in (mijoz AI gapirayotganда gapira boshlasa, AI to'xtaydi) — kodда bor
- NF-3: Bir vaqtда kamida 5 parallel qo'ng'iroq
- NF-4: Maxfiylik: audio/transkript shifrlangan storage, kirish nazorati, audit
- NF-5: Real bemor ma'lumoti faqat zarur joyда; kodда sir saqlanmaydi
- NF-6: Til: foydalanuvchi UI va ovoz uz/rus; ingliz yo'q

## 8. Ma'lumotlar modeli (mavjudni kengaytirish)

- `CallSession` / `TelephonyCall` — qo'ng'iroq metadatasi (mavjud)
- `Transcript` — matn (mavjud)
- `AudioRecording` — audio fayl havolasi (mavjud)
- `Appointment` — qabul (mavjud), source="ai_call"
- `NotificationLog` — SMS audit (mavjud)
- `CallbackTask` — operator callback (mavjud)

## 9. Integratsiya nuqtalari

- Booking: ovozli agent mavjud `AppointmentService`/slot mantig'idan foydalanadi
- SMS: mavjud `NotificationService` (Eskiz/mock)
- Bilim bazasi: mavjud RAG/KB; real klinika ma'lumoti kiritiladi
- Xavfsizlik: mavjud `SafetyGuardService` (kuchaytiriladi)

## 10. Bosqichlar va muddat

| Bosqich | Ish | Taxminiy muddat |
|---|---|---|
| 0. Tayyorgarlik | Raqam/SIP qarori, provider kalitlari, klinika ma'lumoti (Discovery) | 1 hafta (mijozga bog'liq) |
| 1. STT/TTS sifat testi | O'zbek nutqни real audioда o'lchash, provider tanlash | 3-5 kun |
| 2. Telefoniya ulanishi | Raqam -> webhook -> media stream uchidan-uchiga | 4-6 kun |
| 3. To'liq oqim | STT -> Claude -> TTS -> booking/transfer/safety jonli | 5-7 kun |
| 4. Bilim bazasi | Real klinika ma'lumoti, FAQ, narx, shifokorlar | 2-3 kun |
| 5. Test/pilot | 50 test qo'ng'irog'i, sozlash, monitoring | 1 hafta |
| **Jami pilot** | | **~3-4 hafta** |
| 6. Production hardening | Sifat, xatoga chidamlilik, monitoring, masshtab | +1-2 oy |

## 11. Taxminiy xarajatlar (oylik, USD)

- Telefon raqam / SIP: ~$10-30/oy + daqiqasiga ~$0.01-0.02
- STT: ~$0.017/daqiqa; TTS: deyarli arzon
- Claude (suhbat): bir qo'ng'iroq ~$0.02-0.10
- Hosting (Railway): mavjud, ~$5-20/oy
- **Bir 3-4 daqiqalik qo'ng'iroq: ~$0.15-0.35; oylik baza ~$30-80 + ishlatish**

## 12. Mijozdan kerakli ma'lumot (Discovery)

- D-1: Telefon raqam yechimi (mavjud raqam/SIP yoki yangi)
- D-2: Klinika ma'lumoti: manzil, ish vaqti, kontaktlar
- D-3: Xizmatlar va narxlar ro'yxati
- D-4: Shifokorlar: FIO, mutaxassislik, qabul jadvali
- D-5: Kamida 30 ta FAQ (savol-javob)
- D-6: Operatorlar ro'yxati va uzatish telefoni
- D-7: Tibbiy xavfsizlik / javob siyosati (rasmiy)

## 13. Qabul mezonlari (Acceptance)

- A-1: Real raqamga qo'ng'iroq qilinganда AI uz/rus tilида javob beradi
- A-2: 50 test qo'ng'irog'ida kamida 80% qabulга yozish to'g'ri yakunlanadi
- A-3: Favqulodda stsenariyда 100% to'g'ri 103-javob (xavfsizlik testi majburiy)
- A-4: Operatorга uzatish 10 ta stsenariyда to'g'ri ishlaydi
- A-5: Har bir qo'ng'iroq transkripti + audio admin panelда ko'rinadi
- A-6: Javob latency o'rtacha < 1.5 s
- A-7: Telefon raqamlari panelда niqoblanadi, audit yoziladi

## 14. Risklar va kamaytirish

| Risk | Ta'sir | Kamaytirish |
|---|---|---|
| O'zbek STT sifati past | Yuqori | 1-bosqichда erta test; provider solishtirish; fallback operatorга |
| Latency yuqori | O'rta | Streaming STT/TTS (kodда bor), Claude Haiku intent uchun |
| Telefon raqam UZ'да murakkab | Yuqori | Lokal SIP provayder bilan ishlash; erta hal qilish |
| Tibbiy xavfsizlik buzilishi | Kritik | Keyword + LLM ikki bosqichli guard; majburiy testlar |
| Real bemor ma'lumoti maxfiyligi | Yuqori | Shifrlash, kirish nazorati, niqoblash, audit |

## 15. Keyingi qadam

1. Mijoz Discovery ma'lumotini (12-bo'lim) beradi va telefon raqam yechimини
   tanlaydi (D-1)
2. Provider kalitlari olinadi (STT/TTS, telefoniya)
3. 1-bosqich (STT sifat testi) boshlanadi — eng katta noaniqlikни erta o'lchash

---

Tasdiqlash uchun: mijoz ushbu TZ'ni ko'rib, qamrov (3-bo'lim), bosqichlar
(10-bo'lim) va qabul mezonlari (13-bo'lim) bo'yicha rozilik beradi.
