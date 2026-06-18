"""Seed data for a demo clinic (deterministic, bilingual).

Idempotent: skips seeding if the knowledge base already has items.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_item import KnowledgeItem
from app.services.knowledge.service import KBCategory

# Each entry: (category, title, content_uz, content_ru, tags)
_SEED: list[tuple[str, str, str, str, list[str]]] = [
    # --- clinic_info ---
    (KBCategory.CLINIC_INFO.value, "Klinika manzili",
     "Klinika manzili: Toshkent shahri, Chilonzor tumani, Bunyodkor ko'chasi 12.",
     "Адрес клиники: город Ташкент, Чиланзарский район, улица Бунёдкор 12.",
     ["manzil", "address", "адрес", "klinika"]),
    (KBCategory.CLINIC_INFO.value, "Ish vaqti",
     "Klinika dushanbadan shanbagacha 09:00 dan 18:00 gacha ishlaydi. Yakshanba — dam olish kuni.",
     "Клиника работает с понедельника по субботу с 09:00 до 18:00. Воскресенье — выходной.",
     ["ish_vaqti", "hours", "часы", "klinika"]),
    (KBCategory.CLINIC_INFO.value, "Kontaktlar",
     "Telefon: +998 71 200 00 00.",
     "Телефон: +998 71 200 00 00.",
     ["kontakt", "telefon", "телефон", "klinika"]),
    # --- branches ---
    (KBCategory.BRANCHES.value, "Filiallar",
     "Bizda 2 ta filial bor: Chilonzor va Yunusobod.",
     "У нас 2 филиала: Чиланзар и Юнусабад.",
     ["filial", "branch", "филиал"]),
    # --- services_prices (5) ---
    (KBCategory.SERVICES_PRICES.value, "Konsultatsiya narxi",
     "Shifokor konsultatsiyasi narxi: 150 000 so'm.",
     "Стоимость консультации врача: 150 000 сум.",
     ["konsultatsiya", "консультация", "narx", "price", "цена", "xizmat"]),
    (KBCategory.SERVICES_PRICES.value, "UZI narxi",
     "UZI tekshiruvi narxi: 120 000 so'm.",
     "Стоимость УЗИ: 120 000 сум.",
     ["uzi", "узи", "narx", "цена", "xizmat"]),
    (KBCategory.SERVICES_PRICES.value, "Qon tahlili narxi",
     "Umumiy qon tahlili narxi: 80 000 so'm.",
     "Стоимость общего анализа крови: 80 000 сум.",
     ["qon", "tahlil", "анализ", "narx", "цена", "xizmat"]),
    (KBCategory.SERVICES_PRICES.value, "Kardiolog konsultatsiyasi narxi",
     "Kardiolog konsultatsiyasi narxi: 200 000 so'm.",
     "Стоимость консультации кардиолога: 200 000 сум.",
     ["kardiolog", "кардиолог", "narx", "цена", "xizmat"]),
    (KBCategory.SERVICES_PRICES.value, "Stomatolog ko'rigi narxi",
     "Stomatolog ko'rigi narxi: 100 000 so'm.",
     "Стоимость осмотра стоматолога: 100 000 сум.",
     ["stomatolog", "стоматолог", "tish", "narx", "цена", "xizmat"]),
    # --- doctors (5) ---
    (KBCategory.DOCTORS.value, "Dr. Aliyev — Kardiolog",
     "Dr. Aliyev — kardiolog, 10 yillik tajriba.",
     "Доктор Алиев — кардиолог, 10 лет опыта.",
     ["aliyev", "kardiolog", "кардиолог", "shifokor", "врач"]),
    (KBCategory.DOCTORS.value, "Dr. Karimova — Stomatolog",
     "Dr. Karimova — stomatolog, 8 yillik tajriba.",
     "Доктор Каримова — стоматолог, 8 лет опыта.",
     ["karimova", "stomatolog", "стоматолог", "shifokor", "врач"]),
    (KBCategory.DOCTORS.value, "Dr. Tosheva — Pediatr",
     "Dr. Tosheva — pediatr, 12 yillik tajriba.",
     "Доктор Тошева — педиатр, 12 лет опыта.",
     ["tosheva", "pediatr", "педиатр", "shifokor", "врач"]),
    (KBCategory.DOCTORS.value, "Dr. Yusupov — Dermatolog",
     "Dr. Yusupov — dermatolog, 7 yillik tajriba.",
     "Доктор Юсупов — дерматолог, 7 лет опыта.",
     ["yusupov", "dermatolog", "дерматолог", "shifokor", "врач"]),
    (KBCategory.DOCTORS.value, "Dr. Saidova — Ginekolog",
     "Dr. Saidova — ginekolog, 9 yillik tajriba.",
     "Доктор Саидова — гинеколог, 9 лет опыта.",
     ["saidova", "ginekolog", "гинеколог", "shifokor", "врач"]),
    # --- doctor_schedule ---
    (KBCategory.DOCTOR_SCHEDULE.value, "Kardiolog qabul jadvali",
     "Kardiolog Dr. Aliyev qabuli: dushanba-juma, 09:00-14:00.",
     "Приём кардиолога доктора Алиева: понедельник-пятница, 09:00-14:00.",
     ["kardiolog", "кардиолог", "aliyev", "jadval", "schedule"]),
    (KBCategory.DOCTOR_SCHEDULE.value, "Stomatolog qabul jadvali",
     "Stomatolog Dr. Karimova qabuli: dushanba-shanba, 10:00-17:00.",
     "Приём стоматолога доктора Каримовой: понедельник-суббота, 10:00-17:00.",
     ["stomatolog", "стоматолог", "karimova", "jadval", "schedule"]),
    # --- faq (10) ---
    (KBCategory.FAQ.value, "Navbatga yozilish",
     "Navbatga telefon orqali yoki klinikaga kelib yozilishingiz mumkin.",
     "Записаться можно по телефону или в клинике.",
     ["navbat", "yozilish", "запись", "faq"]),
    (KBCategory.FAQ.value, "To'lov usullari",
     "To'lovni naqd yoki plastik karta orqali amalga oshirishingiz mumkin.",
     "Оплата возможна наличными или картой.",
     ["tolov", "оплата", "faq"]),
    (KBCategory.FAQ.value, "Tahlil natijalari",
     "Tahlil natijalari odatda 1-2 ish kunida tayyor bo'ladi.",
     "Результаты анализов обычно готовы через 1-2 рабочих дня.",
     ["natija", "результат", "faq"]),
    (KBCategory.FAQ.value, "Bolalar qabuli",
     "Bizda bolalar uchun pediatr qabuli mavjud.",
     "У нас есть приём педиатра для детей.",
     ["bolalar", "pediatr", "дети", "faq"]),
    (KBCategory.FAQ.value, "Avtoturargoh",
     "Klinika oldida bepul avtoturargoh mavjud.",
     "Перед клиникой есть бесплатная парковка.",
     ["avtoturargoh", "parkovka", "парковка", "faq"]),
    (KBCategory.FAQ.value, "Hujjatlar",
     "Qabulga pasport yoki tug'ilganlik guvohnomasini olib keling.",
     "На приём возьмите паспорт или свидетельство о рождении.",
     ["hujjat", "pasport", "документ", "faq"]),
    (KBCategory.FAQ.value, "Onlayn konsultatsiya",
     "Hozircha onlayn konsultatsiya xizmati mavjud emas.",
     "Онлайн-консультация пока недоступна.",
     ["onlayn", "онлайн", "faq"]),
    (KBCategory.FAQ.value, "Aksiyalar",
     "Joriy aksiyalar haqida operator orqali ma'lumot olishingiz mumkin.",
     "Об актуальных акциях можно узнать у оператора.",
     ["aksiya", "акция", "faq"]),
    (KBCategory.FAQ.value, "Tilni tanlash",
     "Biz o'zbek va rus tillarida xizmat ko'rsatamiz.",
     "Мы обслуживаем на узбекском и русском языках.",
     ["til", "язык", "faq"]),
    (KBCategory.FAQ.value, "Navbatni bekor qilish",
     "Navbatni telefon orqali bekor qilishingiz mumkin.",
     "Запись можно отменить по телефону.",
     ["bekor", "отмена", "faq"]),
    # --- preparation_instructions (5) ---
    (KBCategory.PREPARATION_INSTRUCTIONS.value, "Qon tahliliga tayyorgarlik",
     "Qon tahliliga och qoringa keling, 8-12 soat ovqat yemang.",
     "На анализ крови приходите натощак, не ешьте 8-12 часов.",
     ["qon", "tahlil", "tayyorgarlik", "подготовка", "анализ"]),
    (KBCategory.PREPARATION_INSTRUCTIONS.value, "UZI ga tayyorgarlik",
     "Qorin bo'shlig'i UZI sidan oldin 6 soat ovqat yemang.",
     "Перед УЗИ брюшной полости не ешьте 6 часов.",
     ["uzi", "узи", "tayyorgarlik", "подготовка"]),
    (KBCategory.PREPARATION_INSTRUCTIONS.value, "Siydik tahliliga tayyorgarlik",
     "Siydik tahliliga ertalabki namunani olib keling.",
     "На анализ мочи принесите утреннюю порцию.",
     ["siydik", "моча", "tayyorgarlik", "подготовка"]),
    (KBCategory.PREPARATION_INSTRUCTIONS.value, "Glyukoza testiga tayyorgarlik",
     "Glyukoza testidan oldin 8 soat och qoling.",
     "Перед тестом на глюкозу воздержитесь от еды 8 часов.",
     ["glyukoza", "глюкоза", "tayyorgarlik", "подготовка"]),
    (KBCategory.PREPARATION_INSTRUCTIONS.value, "EKG ga tayyorgarlik",
     "EKG dan oldin jismoniy zo'riqishdan saqlaning.",
     "Перед ЭКГ избегайте физических нагрузок.",
     ["ekg", "экг", "tayyorgarlik", "подготовка"]),
    # --- operator_rules ---
    (KBCategory.OPERATOR_RULES.value, "Operatorga ulash qoidasi",
     "Murakkab, tibbiy yoki noaniq holatlarda qo'ng'iroq operatorga uzatiladi.",
     "В сложных, медицинских или неясных случаях звонок передаётся оператору.",
     ["operator", "оператор", "rules"]),
    # --- emergency_policy ---
    (KBCategory.EMERGENCY_POLICY.value, "Favqulodda holat siyosati",
     "Favqulodda tibbiy holatda darhol 103 raqamiga qo'ng'iroq qiling yoki eng yaqin "
     "shifoxonaga murojaat qiling.",
     "В экстренной медицинской ситуации немедленно звоните по номеру 103 или обратитесь "
     "в ближайшую больницу.",
     ["favqulodda", "103", "emergency", "экстренн"]),
]


async def seed_demo_clinic(session: AsyncSession, *, force: bool = False) -> int:
    """Insert demo KB items. Returns the number inserted (0 if already seeded)."""
    if not force:
        existing = await session.scalar(select(func.count()).select_from(KnowledgeItem))
        if existing:
            return 0

    session.add_all(
        KnowledgeItem(
            category=cat, title=title, content_uz=uz, content_ru=ru, tags=tags, is_active=True
        )
        for (cat, title, uz, ru, tags) in _SEED
    )
    await session.flush()
    return len(_SEED)
