export type Lang = "uz" | "ru";

export const translations = {
  uz: {
    nav: {
      home: "Bosh sahifa",
      services: "Xizmatlar",
      doctors: "Shifokorlar",
      ai: "AI yordamchi",
      faq: "Savollar",
      contact: "Aloqa",
      book: "Qabulga yozilish",
    },
    hero: {
      badge: "24/7 AI telefon yordamchi",
      title: "Ishonchli tibbiy xizmat",
      highlight: "urologiya klinikasi",
      desc: "Zamonaviy uskunalar, malakali mutaxassislar va AI yordamchi. Qabul uchun qo'ng'iroq qiling yoki saytdan so'rov qoldiring.",
      btnBook: "Qabulga yozilish",
      btnCall: "Qo'ng'iroq qilish",
      cardDoc: "Mutaxassis urolog",
      cardDocSub: "Navbat mavjud",
      cardAI: "AI yordamchi faol",
      cardAISub: "24/7 ishlayapti",
      cardAppt: "Qabul tasdiqlandi",
      cardApptSub: "Ertaga 10:00",
    },
    trust: {
      title: "Nima uchun biz?",
      items: [
        { title: "Tajribali shifokorlar",   desc: "Yuqori malakali urolog mutaxassislar" },
        { title: "Zamonaviy diagnostika",   desc: "Ilg'or tibbiy uskunalar va texnologiyalar" },
        { title: "Maxfiylik",               desc: "Bemor ma'lumotlari qat'iy himoyalangan" },
        { title: "Qulay jadval",            desc: "Sizga qulay vaqtda qabul imkoniyati" },
        { title: "AI aloqa 24/7",          desc: "Tezkor ma'lumot va qabul yozish" },
      ],
    },
    services: {
      title: "Bizning xizmatlar",
      sub: "Yuqori sifatli urologik tibbiy xizmatlar",
      items: [
        { title: "Urolog konsultatsiyasi",    desc: "Malakali urolog shifokor bilan batafsil ko'rik va maslahat." },
        { title: "UZI diagnostikasi",         desc: "Buyrak, siydik pufagi va prostata ultratovush tekshiruvi." },
        { title: "Laborator tahlillar",       desc: "Keng qamrovli qon, siydik va boshqa tahlillar." },
        { title: "Profilaktik ko'rik",        desc: "Kasalliklarni erta aniqlash va profilaktika ko'rigi." },
        { title: "Siydik yo'llari tekshiruvi", desc: "Siydik yo'llari kasalliklarini tashxislash va kuzatuv." },
        { title: "Endoskopik tekshiruvlar",   desc: "Zamonaviy endoskopik diagnostika usullari." },
      ],
    },
    ai: {
      title: "AI telefon yordamchi",
      sub: "Klinikamiz zamonaviy AI texnologiyasi bilan jihozlangan",
      features: [
        "Qo'ng'iroqlarni 24/7 qabul qiladi",
        "Xizmatlar va ish vaqti haqida ma'lumot beradi",
        "Qabul uchun so'rov qabul qiladi va yo'naltiradi",
        "Murakkab savollar uchun operatorga ulaydi",
        "Tibbiy maslahat talab qiladigan holatlarni shifokorga yo'naltiradi",
      ],
      safety:
        "AI yordamchi diagnoz qo'ymaydi, dori tavsiya qilmaydi va davolash rejasi bermaydi. Tibbiy maslahat uchun doimo shifokorga murojaat qiling. Favqulodda holatda 103 raqamiga qo'ng'iroq qiling.",
      btn: "AI bilan suhbatlash",
      cardTitle: "AI yordamchi",
      cardStatus: "Faol — 24/7",
      cardLine1: "Salom! Qabul yozishga yordam bera olaman.",
      cardLine2: "Bugun bo'sh vaqtlar mavjud.",
    },
    doctors: {
      title: "Bizning shifokorlar",
      sub: "Malakali mutaxassislar jamoasi",
      cards: [
        { init: "UA", name: "Dr. [Ism Familiya]", spec: "Urolog",         exp: "10+ yil tajriba", sched: "Du–Ju | 09:00–17:00" },
        { init: "UB", name: "Dr. [Ism Familiya]", spec: "Urolog-hirurg",  exp: "8+ yil tajriba",  sched: "Se–Shan | 10:00–18:00" },
        { init: "UC", name: "Dr. [Ism Familiya]", spec: "Pediatrik urolog", exp: "12+ yil tajriba", sched: "Du–Ju | 08:00–16:00" },
      ],
      btn: "Qabulga yozilish",
    },
    flow: {
      title: "Qabulga yozilish tartibi",
      sub: "Oson va qulay — 3 qadam",
      steps: [
        { n: "1", title: "Qo'ng'iroq qiling",       desc: "Telefon raqamimizga qo'ng'iroq qiling yoki saytdan so'rov qoldiring." },
        { n: "2", title: "AI yordamchi ishlaydi",    desc: "AI yordamchi kerakli ma'lumotni aniqlab, mos shifokorga yo'naltiradi." },
        { n: "3", title: "Qabul tasdiqlandi",        desc: "Operator qabul vaqtini tasdiqlaydi va eslatma yuboradi." },
      ],
    },
    faq: {
      title: "Ko'p beriladigan savollar",
      items: [
        {
          q: "Qabulga qanday yozilaman?",
          a: "Telefon orqali qo'ng'iroq qilishingiz yoki saytdagi AI yordamchi orqali so'rov qoldirishingiz mumkin. Operator siz bilan qabul vaqtini kelishib oladi.",
        },
        {
          q: "AI yordamchi nima qila oladi?",
          a: "AI yordamchi xizmatlar va ish vaqti haqida ma'lumot beradi, qabul uchun so'rov qabul qiladi va operatorga ulaydi. Murakkab savollar uchun doimo tirik operator va shifokor mavjud.",
        },
        {
          q: "AI tibbiy maslahat beradimi?",
          a: "Yo'q. AI yordamchi hech qanday tibbiy maslahat bermaydi, diagnoz qo'ymaydi va dori tavsiya qilmaydi. Bunday savollar shifokorga yo'naltiriladi.",
        },
        {
          q: "Shifokor bilan qanday bog'lanaman?",
          a: "Qabul vaqtini olish uchun telefon orqali murojaat qiling yoki saytdan so'rov qoldiring. Qabul davomida shifokor bilan bevosita muloqot qilasiz.",
        },
        {
          q: "Ma'lumotlarim xavfsizmi?",
          a: "Ha. Barcha bemor ma'lumotlari qat'iy maxfiylik bilan saqlanadi va uchinchi shaxslarga berilmaydi.",
        },
      ],
    },
    contact: {
      title: "Biz bilan bog'laning",
      sub: "Savolingiz bo'lsa, murojaat qiling",
      phone: "Telefon",
      addr: "Manzil",
      hours: "Ish vaqti",
      phoneVal: "+998 71 XXX XX XX",
      addrVal: "Toshkent sh., [tuman], [ko'cha, uy]",
      hoursVal: "Du–Ju: 08:00–20:00  |  Shan: 09:00–17:00  |  Yak: 10:00–14:00",
      fName: "Ismingiz",
      fPhone: "Telefon raqamingiz",
      fMsg: "Xabar (ixtiyoriy)",
      fBtn: "Yuborish",
      fSent: "So'rovingiz qabul qilindi. Tez orada operatorimiz siz bilan bog'lanadi.",
      mapLabel: "Xarita",
    },
    footer: {
      tagline: "Ishonchli urologik tibbiy xizmat",
      pages: "Sahifalar",
      contacts: "Aloqa",
      privacy: "Maxfiylik siyosati",
      staff: "Xodimlar uchun kirish",
      safety:
        "Saytdagi ma'lumotlar umumiy ma'lumot uchun mo'ljallangan. Diagnoz qo'yish va davolash bo'yicha shifokorga murojaat qiling. Favqulodda holatda 103 ga qo'ng'iroq qiling.",
      copy: "© 2025 UroCare. Barcha huquqlar himoyalangan.",
    },
  },

  ru: {
    nav: {
      home: "Главная",
      services: "Услуги",
      doctors: "Врачи",
      ai: "AI-ассистент",
      faq: "Вопросы",
      contact: "Контакты",
      book: "Записаться",
    },
    hero: {
      badge: "Круглосуточный AI телефонный ассистент",
      title: "Надёжная медицинская помощь",
      highlight: "урологическая клиника",
      desc: "Современное оборудование, квалифицированные специалисты и AI-ассистент. Запишитесь на приём по телефону или через сайт.",
      btnBook: "Записаться на приём",
      btnCall: "Позвонить",
      cardDoc: "Специалист-уролог",
      cardDocSub: "Есть свободные записи",
      cardAI: "AI-ассистент активен",
      cardAISub: "Работает 24/7",
      cardAppt: "Приём подтверждён",
      cardApptSub: "Завтра 10:00",
    },
    trust: {
      title: "Почему мы?",
      items: [
        { title: "Опытные врачи",           desc: "Команда высококвалифицированных урологов" },
        { title: "Современная диагностика",  desc: "Передовое медицинское оборудование" },
        { title: "Конфиденциальность",       desc: "Данные пациентов строго защищены" },
        { title: "Удобное расписание",       desc: "Приём в удобное для вас время" },
        { title: "AI-связь 24/7",           desc: "Быстрая информация и запись" },
      ],
    },
    services: {
      title: "Наши услуги",
      sub: "Высококачественные урологические медицинские услуги",
      items: [
        { title: "Консультация уролога",           desc: "Подробный осмотр и консультация квалифицированного уролога." },
        { title: "УЗИ диагностика",                desc: "УЗИ почек, мочевого пузыря и предстательной железы." },
        { title: "Лабораторные анализы",           desc: "Широкий спектр анализов крови, мочи и других исследований." },
        { title: "Профилактический осмотр",        desc: "Раннее выявление и профилактика урологических заболеваний." },
        { title: "Диагностика мочевыводящих путей", desc: "Диагностика и наблюдение заболеваний мочевыводящих путей." },
        { title: "Эндоскопические исследования",   desc: "Современные методы эндоскопической диагностики." },
      ],
    },
    ai: {
      title: "AI телефонный ассистент",
      sub: "Наша клиника оснащена современными AI-технологиями",
      features: [
        "Принимает звонки 24/7",
        "Предоставляет информацию об услугах и расписании",
        "Принимает заявки на запись и направляет",
        "Переключает на оператора для сложных вопросов",
        "Направляет медицинские вопросы к врачу",
      ],
      safety:
        "AI-ассистент не ставит диагнозы, не рекомендует лекарства и не составляет план лечения. По медицинским вопросам всегда обращайтесь к врачу. В экстренных случаях звоните 103.",
      btn: "Написать AI-ассистенту",
      cardTitle: "AI-ассистент",
      cardStatus: "Активен — 24/7",
      cardLine1: "Здравствуйте! Могу помочь записаться на приём.",
      cardLine2: "На сегодня есть свободное время.",
    },
    doctors: {
      title: "Наши врачи",
      sub: "Команда квалифицированных специалистов",
      cards: [
        { init: "UA", name: "Д-р [Имя Фамилия]", spec: "Уролог",          exp: "Опыт 10+ лет", sched: "Пн–Пт | 09:00–17:00" },
        { init: "UB", name: "Д-р [Имя Фамилия]", spec: "Уролог-хирург",   exp: "Опыт 8+ лет",  sched: "Ср–Сб | 10:00–18:00" },
        { init: "UC", name: "Д-р [Имя Фамилия]", spec: "Детский уролог",  exp: "Опыт 12+ лет", sched: "Пн–Пт | 08:00–16:00" },
      ],
      btn: "Записаться",
    },
    flow: {
      title: "Как записаться на приём",
      sub: "Просто и удобно — 3 шага",
      steps: [
        { n: "1", title: "Позвоните или оставьте заявку", desc: "Позвоните по номеру клиники или оставьте заявку на сайте." },
        { n: "2", title: "AI-ассистент обработает запрос", desc: "AI уточнит информацию и направит к нужному специалисту." },
        { n: "3", title: "Приём подтверждён",              desc: "Оператор подтвердит время приёма и пришлёт напоминание." },
      ],
    },
    faq: {
      title: "Часто задаваемые вопросы",
      items: [
        {
          q: "Как записаться на приём?",
          a: "Вы можете позвонить по номеру клиники или оставить заявку через AI-ассистент на сайте. Оператор свяжется с вами для уточнения времени.",
        },
        {
          q: "Что умеет AI-ассистент?",
          a: "AI-ассистент предоставляет информацию об услугах и расписании, принимает заявки на запись и переключает на оператора. Для сложных вопросов всегда доступен живой оператор и врач.",
        },
        {
          q: "Даёт ли AI медицинские советы?",
          a: "Нет. AI-ассистент не даёт медицинских советов, не ставит диагнозы и не рекомендует лекарства. Такие вопросы направляются к врачу.",
        },
        {
          q: "Как связаться с врачом?",
          a: "Для консультации запишитесь на приём по телефону или через сайт. На приёме вы сможете напрямую поговорить с врачом.",
        },
        {
          q: "Мои данные в безопасности?",
          a: "Да. Все данные пациентов хранятся строго конфиденциально и не передаются третьим лицам.",
        },
      ],
    },
    contact: {
      title: "Свяжитесь с нами",
      sub: "Если у вас есть вопросы, обращайтесь",
      phone: "Телефон",
      addr: "Адрес",
      hours: "Часы работы",
      phoneVal: "+998 71 XXX XX XX",
      addrVal: "г. Ташкент, [район], [улица, дом]",
      hoursVal: "Пн–Пт: 08:00–20:00  |  Сб: 09:00–17:00  |  Вс: 10:00–14:00",
      fName: "Ваше имя",
      fPhone: "Номер телефона",
      fMsg: "Сообщение (необязательно)",
      fBtn: "Отправить",
      fSent: "Ваша заявка принята. Наш оператор свяжется с вами в ближайшее время.",
      mapLabel: "Карта",
    },
    footer: {
      tagline: "Надёжная урологическая медицинская помощь",
      pages: "Страницы",
      contacts: "Контакты",
      privacy: "Политика конфиденциальности",
      staff: "Вход для сотрудников",
      safety:
        "Информация на сайте носит общий ознакомительный характер. По вопросам диагностики и лечения обращайтесь к врачу. В экстренных случаях звоните 103.",
      copy: "© 2025 UroCare. Все права защищены.",
    },
  },
};

export type Translations = typeof translations.uz;
