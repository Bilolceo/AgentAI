"use client";

// Frontend i18n: Uzbek (default) + Russian. User-facing UI text only; code
// identifiers / enum codes / API values stay English. Selected locale persists
// in localStorage. English backend enum codes are translated at render time via
// tStatus().
import React, { createContext, useContext, useEffect, useState } from "react";

export type Locale = "uz" | "ru";

export const LOCALES: { value: Locale; label: string }[] = [
  { value: "uz", label: "O'zbek" },
  { value: "ru", label: "Русский" },
];

const STORAGE_KEY = "ui_locale";

type Entry = { uz: string; ru: string };

// --- UI string dictionary ---------------------------------------------------
const DICT: Record<string, Entry> = {
  // common
  loading: { uz: "Yuklanmoqda...", ru: "Загрузка..." },
  error: { uz: "Xatolik", ru: "Ошибка" },
  no_data: { uz: "Ma'lumot yo'q", ru: "Нет данных" },
  yes: { uz: "Ha", ru: "Да" },
  no: { uz: "Yo'q", ru: "Нет" },
  enabled: { uz: "yoqilgan", ru: "включено" },
  disabled: { uz: "o'chirilgan", ru: "выключено" },
  details: { uz: "Batafsil", ru: "Подробнее" },
  logout: { uz: "Chiqish", ru: "Выход" },
  checking_session: { uz: "Sessiya tekshirilmoqda...", ru: "Проверка сессии..." },
  admin_required: { uz: "admin huquqi talab qilinadi", ru: "требуется роль администратора" },
  metrics_admin_only: {
    uz: "klinika ko'rsatkichlari admin huquqini talab qiladi",
    ru: "метрики клиники доступны только администратору",
  },
  safety_label: { uz: "Tibbiy xavfsizlik:", ru: "Медицинская безопасность:" },
  safety_notice: {
    uz: "AI yordamchi diagnoz qo'ymaydi, dori tavsiya qilmaydi, tahlil natijalarini izohlamaydi va davolash rejasi bermaydi. Xavfli tibbiy savollar operatorga yoki shoshilinch yordamga yo'naltirilishi shart.",
    ru: "AI-ассистент не ставит диагноз, не рекомендует лекарства, не интерпретирует результаты анализов и не составляет план лечения. Небезопасные медицинские вопросы должны эскалироваться оператору или к экстренной помощи.",
  },

  // site header
  brand: { uz: "Urologiya klinikasi", ru: "Урологическая клиника" },
  nav_sim: { uz: "Simulyatsiya", ru: "Симуляция" },
  nav_admin: { uz: "Boshqaruv", ru: "Управление" },

  // admin shell
  shell_title: { uz: "Urologiya klinikasi", ru: "Урологическая клиника" },
  shell_sub: { uz: "AI registrator — boshqaruv", ru: "AI регистратор — управление" },
  grp_overview: { uz: "Boshqaruv paneli", ru: "Панель управления" },
  grp_calls: { uz: "Qo'ng'iroqlar", ru: "Звонки" },
  grp_voice: { uz: "Ovoz tizimi", ru: "Голосовая система" },
  grp_content: { uz: "Klinika kontenti", ru: "Контент клиники" },
  grp_ops: { uz: "Operatsiyalar", ru: "Операции" },
  grp_security: { uz: "Xavfsizlik", ru: "Безопасность" },
  nav_overview: { uz: "Boshqaruv paneli", ru: "Панель управления" },
  nav_call_history: { uz: "Qo'ng'iroqlar tarixi", ru: "История звонков" },
  nav_telephony: { uz: "Telefoniya qo'ng'iroqlari", ru: "Телефонные звонки" },
  nav_readiness: { uz: "Tizim tayyorligi", ru: "Готовность системы" },
  nav_audio: { uz: "Audio yozuvlar", ru: "Аудиозаписи" },
  nav_kb: { uz: "Bilimlar bazasi", ru: "База знаний" },
  nav_callbacks: { uz: "Operator navbati", ru: "Очередь оператора" },
  nav_audit: { uz: "Audit jurnali", ru: "Журнал аудита" },
  nav_security: { uz: "Xavfsizlik (2FA)", ru: "Безопасность (2FA)" },
  nav_users: { uz: "Foydalanuvchilar", ru: "Пользователи" },
  role_super_admin: { uz: "Bosh administrator", ru: "Главный администратор" },
  role_admin: { uz: "Administrator", ru: "Администратор" },
  role_operator: { uz: "Operator", ru: "Оператор" },

  // landing
  home_title: { uz: "Bosh sahifa", ru: "Главная" },
  home_intro: {
    uz: "Pilot MVP — matnli qo'ng'iroq simulyatsiyasi. Qo'ng'iroqlar tarixi, transkriptlar va bronlar shu yerda ko'rsatiladi.",
    ru: "Пилотный MVP — текстовая симуляция звонков. История звонков, транскрипты и записи отображаются здесь.",
  },
  home_card_calls: { uz: "Qo'ng'iroqlar", ru: "Звонки" },
  home_card_calls_hint: { uz: "Tarix va transkriptlar", ru: "История и транскрипты" },
  home_card_kb: { uz: "Bilimlar bazasi", ru: "База знаний" },
  home_card_kb_hint: { uz: "Klinika ma'lumotlari", ru: "Информация клиники" },
  home_card_sim: { uz: "Simulyatsiya", ru: "Симуляция" },
  home_card_sim_hint: { uz: "AI bilan matnli test", ru: "Текстовый тест с AI" },

  // login
  login_title: { uz: "Tizimga kirish", ru: "Вход в систему" },
  login_email: { uz: "Email", ru: "Email" },
  login_password: { uz: "Parol", ru: "Пароль" },
  login_signin: { uz: "Kirish", ru: "Войти" },
  login_please_wait: { uz: "Iltimos kuting...", ru: "Подождите..." },
  login_2fa_hint: {
    uz: "6 xonali kodingizni yoki tiklash kodini kiriting.",
    ru: "Введите 6-значный код или код восстановления.",
  },
  login_auth_code: { uz: "Tasdiqlash kodi", ru: "Код подтверждения" },
  login_verify: { uz: "Tasdiqlash", ru: "Подтвердить" },
  login_failed: { uz: "Kirish amalga oshmadi", ru: "Не удалось войти" },
  login_invalid_code: { uz: "Noto'g'ri kod", ru: "Неверный код" },

  // change password
  cp_title: { uz: "Parolni o'zgartirish", ru: "Смена пароля" },
  cp_intro: {
    uz: "Davom etishdan oldin yangi parol o'rnating. Kamida 10 ta belgi, harf va raqam bilan.",
    ru: "Перед продолжением задайте новый пароль. Минимум 10 символов, с буквой и цифрой.",
  },
  cp_current: { uz: "Joriy parol", ru: "Текущий пароль" },
  cp_new: { uz: "Yangi parol", ru: "Новый пароль" },
  cp_submit: { uz: "Parolni o'zgartirish", ru: "Сменить пароль" },
  cp_saving: { uz: "Saqlanmoqda...", ru: "Сохранение..." },
  failed_generic: { uz: "Amalga oshmadi", ru: "Не удалось" },

  // security / 2FA
  sec_title: { uz: "Ikki bosqichli autentifikatsiya", ru: "Двухфакторная аутентификация" },
  sec_status: { uz: "Holat", ru: "Статус" },
  sec_enabled: { uz: "Yoqilgan", ru: "Включено" },
  sec_disabled: { uz: "O'chirilgan", ru: "Выключено" },
  sec_recovery_title: { uz: "Tiklash kodlari (hozir saqlang)", ru: "Коды восстановления (сохраните сейчас)" },
  sec_start: { uz: "Sozlashni boshlash", ru: "Начать настройку" },
  sec_add_secret: {
    uz: "Bu maxfiy kalitni autentifikator ilovangizga qo'shing:",
    ru: "Добавьте этот секретный ключ в приложение-аутентификатор:",
  },
  sec_6digit: { uz: "6 xonali kod", ru: "6-значный код" },
  sec_confirm_enable: { uz: "Tasdiqlash va yoqish", ru: "Подтвердить и включить" },
  sec_current_or_recovery: { uz: "Joriy 6 xonali yoki tiklash kodi", ru: "Текущий 6-значный или код восстановления" },
  sec_regenerate: { uz: "Tiklash kodlarini qayta yaratish", ru: "Пересоздать коды восстановления" },
  sec_disable: { uz: "2FA ni o'chirish", ru: "Отключить 2FA" },

  // calls list + detail
  calls_title: { uz: "Qo'ng'iroqlar tarixi", ru: "История звонков" },
  filter_all: { uz: "hammasi", ru: "все" },
  th_duration: { uz: "Davomiyligi", ru: "Длительность" },
  empty_calls_filter: { uz: "Filtrlarga mos qo'ng'iroq yo'q.", ru: "Нет звонков по этим фильтрам." },
  detail_back: { uz: "Qo'ng'iroqlarga qaytish", ru: "Назад к звонкам" },
  detail_call: { uz: "Qo'ng'iroq", ru: "Звонок" },
  lbl_priority: { uz: "muhimlik", ru: "приоритет" },
  lbl_reason: { uz: "sabab", ru: "причина" },
  lbl_phone: { uz: "telefon", ru: "телефон" },
  lbl_due: { uz: "muddat", ru: "срок" },
  transfer_label: { uz: "Uzatish", ru: "Передача" },
  safety_codes: { uz: "Xavfsizlik sabab kodlari", ru: "Коды причин безопасности" },
  callback_task: { uz: "Qayta qo'ng'iroq vazifasi", ru: "Задача обратного звонка" },
  transcript: { uz: "Transkript", ru: "Транскрипт" },
  kb_sources_used: { uz: "Ishlatilgan bilim manbalari", ru: "Использованные источники" },

  // table headers (shared)
  th_call: { uz: "Qo'ng'iroq", ru: "Звонок" },
  th_phone: { uz: "Telefon", ru: "Телефон" },
  th_reason: { uz: "Sabab", ru: "Причина" },
  th_priority: { uz: "Muhimlik", ru: "Приоритет" },
  th_due: { uz: "Muddat", ru: "Срок" },
  th_assigned: { uz: "Tayinlangan", ru: "Назначен" },
  th_actions: { uz: "Amallar", ru: "Действия" },
  th_provider: { uz: "Provayder", ru: "Провайдер" },
  th_provider_call_id: { uz: "Provayder qo'ng'iroq ID", ru: "ID звонка провайдера" },
  th_direction: { uz: "Yo'nalish", ru: "Направление" },
  th_to: { uz: "Kimga", ru: "Кому" },
  th_created: { uz: "Yaratilgan", ru: "Создан" },

  // callbacks
  cb_title: { uz: "Operator navbati", ru: "Очередь оператора" },
  cb_empty: { uz: "Qayta qo'ng'iroq vazifalari yo'q.", ru: "Нет задач обратного звонка." },
  ph_reason: { uz: "Sabab", ru: "Причина" },
  chk_assigned_me: { uz: "menga tayinlangan", ru: "назначено мне" },
  overdue: { uz: "muddati o'tgan", ru: "просрочено" },
  act_assign_me: { uz: "Menga olish", ru: "Взять себе" },
  act_complete: { uz: "Yakunlash", ru: "Завершить" },
  act_notes: { uz: "Izohlar", ru: "Заметки" },
  act_reschedule: { uz: "Qayta rejalashtirish", ru: "Перенести" },
  act_cancel: { uz: "Bekor qilish", ru: "Отменить" },
  prompt_notes: { uz: "Yechim izohlari:", ru: "Заметки по решению:" },
  prompt_due: { uz: "Yangi muddat (YYYY-MM-DDTHH:MM):", ru: "Новый срок (YYYY-MM-DDTHH:MM):" },
  confirm_cancel: { uz: "Ushbu qayta qo'ng'iroqni bekor qilasizmi?", ru: "Отменить этот обратный звонок?" },
  msg_assigned: { uz: "Sizga tayinlandi.", ru: "Назначено вам." },
  msg_completed: { uz: "Yakunlandi.", ru: "Завершено." },
  msg_notes_saved: { uz: "Izohlar saqlandi.", ru: "Заметки сохранены." },
  msg_rescheduled: { uz: "Qayta rejalashtirildi.", ru: "Перенесено." },
  msg_cancelled: { uz: "Bekor qilindi.", ru: "Отменено." },
  action_failed: { uz: "Amal bajarilmadi.", ru: "Действие не удалось." },

  // telephony calls
  tel_title: { uz: "Telefoniya qo'ng'iroqlari", ru: "Телефонные звонки" },
  tel_sub: {
    uz: "Mock telefoniya webhookidan kirish metadatasi. Sirlar hech qachon oshkor qilinmaydi.",
    ru: "Метаданные приёма из mock-вебхука телефонии. Секреты не раскрываются.",
  },
  tel_forbidden: {
    uz: "Taqiqlangan: faqat bosh administrator va administrator ko'ra oladi.",
    ru: "Запрещено: просматривать могут только главный администратор и администратор.",
  },
  ph_call_session_id: { uz: "Qo'ng'iroq sessiyasi ID", ru: "ID сессии звонка" },
  tel_empty: { uz: "Filtrlarga mos telefoniya qo'ng'iroqlari yo'q.", ru: "Нет звонков по этим фильтрам." },
  pg_prev: { uz: "Oldingi", ru: "Назад" },
  pg_next: { uz: "Keyingi", ru: "Далее" },
  pg_rows: { uz: "qatorlar", ru: "строки" },

  // knowledge base
  kb_title: { uz: "Bilimlar bazasi", ru: "База знаний" },
  kb_new: { uz: "Yangi yozuv", ru: "Новая запись" },
  kb_seed: { uz: "Demo klinikani yuklash", ru: "Загрузить демо-клинику" },
  th_title: { uz: "Sarlavha", ru: "Заголовок" },
  th_category: { uz: "Kategoriya", ru: "Категория" },
  th_tags: { uz: "Teglar", ru: "Теги" },
  th_active: { uz: "Faol", ru: "Активный" },
  kb_empty: { uz: "Bilim yozuvlari yo'q.", ru: "Нет записей знаний." },
  kb_active_only: { uz: "faqat faol", ru: "только активные" },
  kb_search: { uz: "Sarlavha yoki tegni qidirish", ru: "Поиск по заголовку или тегу" },
  kb_create: { uz: "Yozuv yaratish", ru: "Создать запись" },
  kb_edit: { uz: "Yozuvni tahrirlash", ru: "Редактировать запись" },
  kb_cat_req: { uz: "Kategoriya majburiy", ru: "Категория обязательна" },
  kb_title_req: { uz: "Sarlavha majburiy", ru: "Заголовок обязателен" },
  kb_content_req: { uz: "O'zbek yoki rus tilida matn kiriting", ru: "Введите текст на узбекском или русском" },
  kb_content_uz: { uz: "Matn (o'zbekcha)", ru: "Текст (узбекский)" },
  kb_content_ru: { uz: "Matn (ruscha)", ru: "Текст (русский)" },
  kb_tags_hint: { uz: "Teglar (vergul bilan)", ru: "Теги (через запятую)" },
  kb_saved: { uz: "Muvaffaqiyatli saqlandi.", ru: "Успешно сохранено." },
  kb_save_failed: { uz: "Saqlash amalga oshmadi", ru: "Не удалось сохранить" },
  kb_seeded: { uz: "Demo klinika yuklandi.", ru: "Демо-клиника загружена." },
  kb_forbidden: {
    uz: "Taqiqlangan: bilimlar bazasini boshqarish administratorlar uchun.",
    ru: "Запрещено: управление базой знаний доступно администраторам.",
  },
  lbl_required: { uz: "majburiy", ru: "обязательно" },
  act_edit: { uz: "Tahrirlash", ru: "Редактировать" },
  act_activate: { uz: "Faollashtirish", ru: "Активировать" },
  act_deactivate: { uz: "Nofaol qilish", ru: "Деактивировать" },
  act_delete: { uz: "O'chirish", ru: "Удалить" },
  act_save: { uz: "Saqlash", ru: "Сохранить" },
  msg_deactivated: { uz: "Nofaol qilindi.", ru: "Деактивировано." },
  msg_activated: { uz: "Faollashtirildi.", ru: "Активировано." },
  msg_deleted: { uz: "O'chirildi.", ru: "Удалено." },

  // users
  users_title: { uz: "Foydalanuvchilar", ru: "Пользователи" },
  users_forbidden: { uz: "Taqiqlangan: faqat bosh administrator.", ru: "Запрещено: только главный администратор." },
  users_empty: { uz: "Foydalanuvchilar yo'q.", ru: "Нет пользователей." },
  th_email: { uz: "Email", ru: "Email" },
  th_full_name: { uz: "To'liq ism", ru: "Полное имя" },
  th_role: { uz: "Rol", ru: "Роль" },
  th_last_login: { uz: "Oxirgi kirish", ru: "Последний вход" },
  u_temp_password: { uz: "Vaqtinchalik parol", ru: "Временный пароль" },
  u_create: { uz: "Yaratish", ru: "Создать" },
  u_reset_pw: { uz: "Parolni tiklash", ru: "Сбросить пароль" },
  u_reset_2fa: { uz: "2FA ni tiklash", ru: "Сбросить 2FA" },
  u_prompt_pw: { uz: "Yangi vaqtinchalik parol:", ru: "Новый временный пароль:" },
  u_confirm_2fa: {
    uz: "2FA tiklansinmi? Foydalanuvchi qayta ro'yxatdan o'tishi kerak.",
    ru: "Сбросить 2FA? Пользователю потребуется повторная регистрация.",
  },

  // audit logs
  audit_title: { uz: "Audit jurnali", ru: "Журнал аудита" },
  audit_forbidden: { uz: "Taqiqlangan: audit jurnali administratorlar uchun.", ru: "Запрещено: журнал аудита доступен администраторам." },
  audit_empty: { uz: "Audit hodisalari yo'q.", ru: "Нет событий аудита." },
  ph_event_type: { uz: "Hodisa turi (masalan login_success)", ru: "Тип события (например login_success)" },
  ph_actor_id: { uz: "Foydalanuvchi ID", ru: "ID пользователя" },
  audit_limit: { uz: "Limit", ru: "Лимит" },
  audit_offset: { uz: "surilish", ru: "смещение" },
  th_event: { uz: "Hodisa", ru: "Событие" },
  th_actor: { uz: "Foydalanuvchi", ru: "Пользователь" },
  th_when: { uz: "Vaqt", ru: "Время" },
  th_metadata: { uz: "Metadata", ru: "Метаданные" },

  // audio recordings
  audio_title: { uz: "Audio yozuvlar", ru: "Аудиозаписи" },
  audio_forbidden: {
    uz: "Taqiqlangan: audio yozuvlarni faqat administratorlar ko'ra oladi.",
    ru: "Запрещено: просматривать аудиозаписи могут только администраторы.",
  },
  audio_sub: {
    uz: "Faqat metadata. Xom audio baytlari bu yerda hech qachon oshkor qilinmaydi.",
    ru: "Только метаданные. Необработанные аудиоданные здесь не раскрываются.",
  },
  audio_empty: { uz: "Filtrlarga mos audio yozuvlar yo'q.", ru: "Нет аудиозаписей по этим фильтрам." },
  ph_call_id: { uz: "Qo'ng'iroq ID", ru: "ID звонка" },
  th_kind: { uz: "Tur", ru: "Тип" },
  chk_include_deleted: { uz: "o'chirilganlar bilan", ru: "включая удалённые" },
  audio_confirm_delete: { uz: "yozuvni yashirasizmi?", ru: "скрыть запись?" },
  audio_deleted_msg: { uz: "yozuv yashirildi.", ru: "запись скрыта." },
  th_content_type: { uz: "Kontent turi", ru: "Тип контента" },
  th_size: { uz: "Hajm", ru: "Размер" },
  th_lang: { uz: "Til", ru: "Язык" },
  th_conf: { uz: "Ishonch", ru: "Увер." },
  th_voice: { uz: "Ovoz", ru: "Голос" },
  th_expires: { uz: "Amal qiladi", ru: "Истекает" },
  th_deleted: { uz: "O'chirilgan", ru: "Удалён" },

  // simulation chat
  sim_hint: {
    uz: "Misol: \"Ish vaqtingiz qanday?\" yoki \"Qaysi dori ichsam bo'ladi?\"",
    ru: "Пример: \"Какой у вас график работы?\" или \"Какое лекарство принять?\"",
  },
  sim_badge_emergency: { uz: "SHOSHILINCH", ru: "ЭКСТРЕННО" },
  sim_badge_operator: { uz: "OPERATORGA", ru: "ОПЕРАТОРУ" },
  sim_input_placeholder: { uz: "Xabar yozing...", ru: "Напишите сообщение..." },
  sim_send: { uz: "Yuborish", ru: "Отправить" },
  sim_title: { uz: "Qo'ng'iroq simulyatsiyasi", ru: "Симуляция звонка" },
  sim_subtitle: {
    uz: "AI qabulxona operatori bilan matnli suhbat. Xavfsizlik to'sig'i (tibbiy maslahat, shoshilinch holat) avtomatik ishlaydi va operatorga uzatadi.",
    ru: "Текстовый диалог с AI-регистратором. Защита (медицинские советы, экстренные случаи) срабатывает автоматически и переводит на оператора.",
  },

  // telephony call detail
  tel_detail_back: { uz: "Telefoniya qo'ng'iroqlariga qaytish", ru: "Назад к телефонным звонкам" },
  tel_call: { uz: "Telefoniya qo'ng'irog'i", ru: "Телефонный звонок" },
  th_call_session: { uz: "Qo'ng'iroq sessiyasi", ru: "Сессия звонка" },
  th_ended: { uz: "Tugadi", ru: "Завершён" },
  th_updated: { uz: "Yangilangan", ru: "Обновлён" },
  act_view_call: { uz: "Qo'ng'iroq tafsilotini ko'rish", ru: "Открыть детали звонка" },
  act_view_audio: { uz: "Audio yozuvlarni ko'rish", ru: "Открыть аудиозаписи" },
  safe_raw_metadata: { uz: "Xavfsiz xom metadata", ru: "Безопасные сырые метаданные" },
  none_paren: { uz: "(yo'q)", ru: "(нет)" },

  // audio recording detail
  audio_detail_back: { uz: "Audio yozuvlarga qaytish", ru: "Назад к аудиозаписям" },
  audio_recording: { uz: "Yozuv", ru: "Запись" },
  deleted_paren: { uz: "(o'chirilgan)", ru: "(удалён)" },
  th_size_bytes: { uz: "Hajm (bayt)", ru: "Размер (байт)" },
  th_duration_ms: { uz: "Davomiyligi (ms)", ru: "Длительность (мс)" },
  th_storage_provider: { uz: "Saqlash provayderi", ru: "Хранилище" },
  th_storage_key: { uz: "Saqlash kaliti", ru: "Ключ хранилища" },
  th_checksum: { uz: "Nazorat summasi (sha256)", ru: "Контрольная сумма (sha256)" },
  th_transcript_lang: { uz: "Transkript tili", ru: "Язык транскрипта" },
  th_transcript_conf: { uz: "Transkript ishonchi", ru: "Увер. транскрипта" },
  audio_transcript_text: { uz: "Transkript matni", ru: "Текст транскрипта" },
  audio_tts_text: { uz: "TTS matni", ru: "Текст TTS" },
  audio_label: { uz: "Audio", ru: "Аудио" },
  audio_open_url: { uz: "Audio URL'ni ochish", ru: "Открыть URL аудио" },
  audio_no_url: { uz: "Ijro etiladigan audio URL mavjud emas.", ru: "Нет доступного URL для воспроизведения." },
  audio_soft_delete: { uz: "Yozuvni yashirish", ru: "Скрыть запись" },

  // --- Manager dashboard (M1a) ---
  mgr_brand_sub: { uz: "Menejer paneli", ru: "Панель менеджера" },
  mgr_nav_home: { uz: "Bosh sahifa", ru: "Главная" },
  mgr_nav_schedule: { uz: "Qabul jadvali", ru: "Расписание приема" },
  mgr_nav_notifications: { uz: "Bildirishnomalar", ru: "Уведомления" },
  mgr_nav_reports: { uz: "Hisobotlar", ru: "Отчеты" },
  mgr_nav_doctors: { uz: "Shifokorlar", ru: "Врачи" },
  mgr_access_denied: { uz: "Bu sahifaga ruxsatingiz yo'q.", ru: "У вас нет доступа к этой странице." },
  mgr_safety: {
    uz: "AI yordamchi diagnoz qo'ymaydi, dori tavsiya qilmaydi va davolash rejasi bermaydi. Shubhali yoki shoshilinch holatlar operator/shifokorga yo'naltiriladi.",
    ru: "AI-ассистент не ставит диагноз, не рекомендует лекарства и не составляет план лечения. Сомнительные или срочные случаи направляются оператору/врачу.",
  },

  // manager home
  mgr_home_title: { uz: "Menejer paneli", ru: "Панель менеджера" },
  mgr_home_sub: { uz: "Klinika kunlik ko'rsatkichlari", ru: "Ежедневные показатели клиники" },
  mgr_kpi_total_calls: { uz: "Jami qo'ng'iroqlar", ru: "Всего звонков" },
  mgr_kpi_ai_resolved: { uz: "AI hal qildi", ru: "Решено AI" },
  mgr_kpi_transfers: { uz: "Operatorga uzatildi", ru: "Передачи оператору" },
  mgr_kpi_action: { uz: "Harakat talab qiladi", ru: "Требует действий" },
  mgr_kpi_appt_today: { uz: "Bugungi qabul", ru: "Приёмы сегодня" },
  mgr_kpi_confirmed: { uz: "Tasdiqlangan", ru: "Подтверждено" },
  mgr_kpi_pending: { uz: "Kutilmoqda", ru: "Ожидает" },
  mgr_kpi_cancelled: { uz: "Bekor qilingan", ru: "Отменено" },
  mgr_kpi_op_required: { uz: "Operatorga kerak", ru: "Требуется оператор" },
  mgr_sec_today_plan: { uz: "Bugungi reja", ru: "План на сегодня" },
  mgr_chart_status: { uz: "Qabullar holati", ru: "Приёмы по статусу" },
  mgr_chart_doctors: { uz: "Shifokorlar bandligi", ru: "Загрузка врачей" },
  mgr_appts: { uz: "qabul", ru: "приёмы" },
  mgr_source_ai: { uz: "AI orqali", ru: "Через AI" },
  mgr_source_other: { uz: "Operator/qo'lda", ru: "Оператор/вручную" },
  mgr_empty_today_plan: { uz: "Bugun qabul rejalashtirilmagan.", ru: "На сегодня приёмы не запланированы." },
  mgr_sec_action_items: { uz: "Harakat talab qiluvchi elementlar", ru: "Требующие действий" },
  mgr_sec_recent_calls: { uz: "So'nggi qo'ng'iroqlar", ru: "Недавние звонки" },
  mgr_empty_action: { uz: "Harakat talab qiluvchi element yo'q.", ru: "Нет элементов, требующих действий." },
  mgr_empty_calls: { uz: "Qo'ng'iroqlar yo'q.", ru: "Звонков нет." },

  // backend-gap (appointment/doctor modules not built yet)
  mgr_gap_appt_title: { uz: "Qabul jadvali moduli", ru: "Модуль расписания приёма" },
  mgr_gap_appt: {
    uz: "Qabul (appointment) ma'lumotlari hali mavjud emas. Bu modul keyingi bosqichda (Appointment/Doctor) qo'shiladi.",
    ru: "Данные о приёмах пока недоступны. Модуль будет добавлен на следующем этапе (Appointment/Doctor).",
  },
  mgr_gap_doctors: {
    uz: "Shifokorlar moduli hali mavjud emas. Keyingi bosqichda (Doctor) qo'shiladi.",
    ru: "Модуль врачей пока недоступен. Будет добавлен на следующем этапе (Doctor).",
  },

  // schedule
  mgr_sched_title: { uz: "Qabul jadvali", ru: "Расписание приема" },
  mgr_view_day: { uz: "Kun", ru: "День" },
  mgr_view_week: { uz: "Hafta", ru: "Неделя" },
  mgr_today: { uz: "Bugun", ru: "Сегодня" },
  mgr_prev: { uz: "Oldingi", ru: "Назад" },
  mgr_next: { uz: "Keyingi", ru: "Вперёд" },
  mgr_empty_day: { uz: "Bugun qabul rejalashtirilmagan", ru: "На сегодня приемы не запланированы" },

  // notifications
  mgr_notif_title: { uz: "Bildirishnomalar", ru: "Уведомления" },
  mgr_notif_empty: { uz: "Bildirishnomalar yo'q.", ru: "Уведомлений нет." },
  mgr_mark_all_read: { uz: "Hammasini o'qilgan deb belgilash", ru: "Отметить все как прочитанные" },
  mgr_mark_read: { uz: "O'qildi", ru: "Прочитано" },
  mgr_unread: { uz: "o'qilmagan", ru: "непрочитанные" },
  ntype_operator_required: { uz: "Operator talab qilinadi", ru: "Требуется оператор" },
  ntype_callback_required: { uz: "Qayta qo'ng'iroq kerak", ru: "Требуется обратный звонок" },
  ntype_callback_overdue: { uz: "Muddati o'tgan qayta qo'ng'iroq", ru: "Просроченный обратный звонок" },
  ntype_emergency: { uz: "Shoshilinch holat", ru: "Экстренный случай" },

  // reports
  mgr_reports_title: { uz: "Hisobotlar", ru: "Отчеты" },
  mgr_rep_action_items: { uz: "Harakat talab qiluvchi elementlar", ru: "Элементы, требующие действий" },
  mgr_rep_note: {
    uz: "Sana bo'yicha (bugun/hafta) hisobotlar Appointment moduli bilan qo'shiladi.",
    ru: "Отчёты по датам (сегодня/неделя) появятся с модулем приёмов.",
  },
  mgr_doctors_title: { uz: "Shifokorlar", ru: "Врачи" },

  // --- Rahbar (director) dashboard ---
  rahbar_brand: { uz: "Klinika rahbari", ru: "Директор клиники" },
  rahbar_brand_sub: { uz: "Boshqaruv paneli", ru: "Панель управления" },
  rahbar_title: { uz: "Klinika rahbari paneli", ru: "Панель директора клиники" },
  rahbar_nav_calendar: { uz: "Kalendar", ru: "Календарь" },
  rahbar_nav_reports: { uz: "Hisobotlar", ru: "Отчёты" },
  rahbar_nav_doctors: { uz: "Shifokorlar", ru: "Врачи" },
  rahbar_nav_notifications: { uz: "Bildirishnomalar", ru: "Уведомления" },
  rahbar_access_denied: { uz: "Bu sahifaga ruxsatingiz yo'q.", ru: "У вас нет доступа к этой странице." },
  rahbar_public_link: { uz: "Onlayn yozilish sahifasi", ru: "Страница онлайн-записи" },
  appt_confirm: { uz: "Tasdiqlash", ru: "Подтвердить" },
  appt_cancel_appt: { uz: "Bekor qilish", ru: "Отменить" },
  appt_mark_arrived: { uz: "Keldi deb belgilash", ru: "Отметить как пришёл" },
  appt_status_updated: { uz: "Qabul holati yangilandi.", ru: "Статус приёма обновлён." },
  kpi_week_total: { uz: "Bu hafta jami", ru: "Всего за неделю" },
  kpi_pending: { uz: "Tasdiq kutmoqda", ru: "Ожидают подтверждения" },
  rahbar_pending_title: { uz: "Tasdiq kutayotgan so'rovlar", ru: "Заявки, ожидающие подтверждения" },
  rahbar_pending_hint: { uz: "Onlayn va qo'lda yozilgan, tasdiqlanmagan qabullar", ru: "Онлайн и ручные записи, ожидающие подтверждения" },
  cal_legend: { uz: "Holatlar", ru: "Статусы" },
  list_title_all: { uz: "Bu hafta barcha qabullar", ru: "Все приёмы за неделю" },
  list_title_confirmed: { uz: "Tasdiqlangan qabullar", ru: "Подтверждённые приёмы" },
  list_title_cancelled: { uz: "Bekor qilingan qabullar", ru: "Отменённые приёмы" },
  list_empty: { uz: "Bu toifada qabul yo'q.", ru: "В этой категории приёмов нет." },
  rahbar_home_sub: { uz: "Klinika faoliyatining umumiy ko'rinishi", ru: "Общий обзор работы клиники" },
  // week calendar
  cal_this_week: { uz: "Shu hafta", ru: "Эта неделя" },
  cal_prev_week: { uz: "Oldingi hafta", ru: "Пред. неделя" },
  cal_next_week: { uz: "Keyingi hafta", ru: "След. неделя" },
  cal_empty_week: { uz: "Bu haftada qabul rejalashtirilmagan.", ru: "На этой неделе приёмов нет." },
  dow_mon: { uz: "Du", ru: "Пн" },
  dow_tue: { uz: "Se", ru: "Вт" },
  dow_wed: { uz: "Cho", ru: "Ср" },
  dow_thu: { uz: "Pa", ru: "Чт" },
  dow_fri: { uz: "Ju", ru: "Пт" },
  dow_sat: { uz: "Sha", ru: "Сб" },
  dow_sun: { uz: "Ya", ru: "Вс" },
  // KPIs
  kpi_week_appts: { uz: "Shu hafta qabullar", ru: "Приёмы на неделе" },
  kpi_today_appts: { uz: "Bugun", ru: "Сегодня" },
  // new appointment form
  new_appt: { uz: "Yangi qabul", ru: "Новый приём" },
  new_appt_title: { uz: "Yangi qabul qo'shish", ru: "Добавить приём" },
  f_patient_name: { uz: "Bemor ismi", ru: "Имя пациента" },
  f_phone: { uz: "Telefon", ru: "Телефон" },
  f_doctor: { uz: "Shifokor", ru: "Врач" },
  f_service: { uz: "Xizmat", ru: "Услуга" },
  f_datetime: { uz: "Sana va vaqt", ru: "Дата и время" },
  f_save: { uz: "Qo'shish", ru: "Добавить" },
  f_cancel: { uz: "Bekor qilish", ru: "Отмена" },
  appt_created: { uz: "Qabul qo'shildi.", ru: "Приём добавлен." },
  appt_required_fields: { uz: "Xizmat va sana/vaqtni kiriting.", ru: "Укажите услугу и дату/время." },
  // notification bell
  notif_bell: { uz: "Bildirishnomalar", ru: "Уведомления" },
  notif_none: { uz: "Yangi bildirishnoma yo'q.", ru: "Новых уведомлений нет." },
  notif_mark_all: { uz: "Hammasini o'qildi", ru: "Прочитать все" },
  ntype_appt_new: { uz: "Yangi qabul", ru: "Новый приём" },
  ntype_appt_cancelled: { uz: "Qabul bekor qilindi", ru: "Приём отменён" },

  // M2 schedule / doctors / reports
  mgr_th_time: { uz: "Vaqt", ru: "Время" },
  mgr_th_patient: { uz: "Bemor", ru: "Пациент" },
  mgr_th_service: { uz: "Xizmat", ru: "Услуга" },
  mgr_th_doctor: { uz: "Shifokor", ru: "Врач" },
  mgr_th_source: { uz: "Manba", ru: "Источник" },
  mgr_th_specialty: { uz: "Mutaxassislik", ru: "Специальность" },
  mgr_th_appointments: { uz: "Qabullar", ru: "Приёмы" },
  mgr_filter_doctor: { uz: "Shifokor", ru: "Врач" },
  mgr_all_doctors: { uz: "Barcha shifokorlar", ru: "Все врачи" },
  mgr_notes_mark: { uz: "izoh", ru: "заметка" },
  mgr_op_required_mark: { uz: "operator", ru: "оператор" },
  mgr_seed_demo: { uz: "Demo ma'lumot yuklash", ru: "Загрузить демо" },
  mgr_seed_done: { uz: "Demo ma'lumot yuklandi.", ru: "Демо-данные загружены." },
  mgr_doctors_empty: { uz: "Shifokorlar yo'q.", ru: "Врачей нет." },
  mgr_workload_today: { uz: "Bugungi bandlik", ru: "Загрузка сегодня" },
  // reports
  mgr_range_today: { uz: "Bugun", ru: "Сегодня" },
  mgr_range_week: { uz: "Hafta", ru: "Неделя" },
  mgr_range_month: { uz: "Oy", ru: "Месяц" },
  mgr_rep_total: { uz: "Jami qabullar", ru: "Всего приёмов" },
  mgr_rep_ai_created: { uz: "AI yaratdi", ru: "Создано AI" },
  mgr_rep_op_required: { uz: "Operator kerak", ru: "Нужен оператор" },
  mgr_rep_cancelled: { uz: "Bekor qilingan", ru: "Отменено" },
  mgr_rep_no_show: { uz: "Kelmaganlar", ru: "Неявки" },
  mgr_rep_by_status: { uz: "Holat bo'yicha", ru: "По статусу" },
  mgr_rep_by_doctor: { uz: "Shifokor bo'yicha", ru: "По врачу" },
  mgr_rep_empty: { uz: "Bu davr uchun ma'lumot yo'q.", ru: "Нет данных за этот период." },

  // overview
  ov_title: { uz: "Boshqaruv paneli", ru: "Панель управления" },
  ov_subtitle: {
    uz: "Urologiya AI registratori — operatsion ko'rsatkichlar",
    ru: "AI регистратор урологии — оперативная сводка",
  },
  m_total_calls: { uz: "Jami qo'ng'iroqlar", ru: "Всего звонков" },
  m_ai_resolved: { uz: "AI hal qildi", ru: "Решено AI" },
  m_operator_transfers: { uz: "Operatorga uzatildi", ru: "Передачи оператору" },
  m_callbacks_required: { uz: "Qayta qo'ng'iroqlar", ru: "Обратные звонки" },
  m_kb_items: { uz: "Bilimlar bazasi", ru: "База знаний" },
  voice_status_title: { uz: "Ovoz tizimi holati", ru: "Состояние голосовой системы" },
  voice_status_sub: {
    uz: "Tayyorlik tekshiruvidan jonli konfiguratsiya",
    ru: "Конфигурация из проверки готовности",
  },
  f_readiness: { uz: "Tayyorlik", ru: "Готовность" },
  f_stt_provider: { uz: "STT provayder", ru: "STT провайдер" },
  f_tts_provider: { uz: "TTS provayder", ru: "TTS провайдер" },
  f_twilio_stt: { uz: "Twilio STT mosligi", ru: "Совместимость Twilio STT" },
  f_twilio_tts: { uz: "Twilio TTS mosligi", ru: "Совместимость Twilio TTS" },
  f_smoke_mode: { uz: "Smoke rejimi", ru: "Smoke-режим" },
  recent_calls: { uz: "So'nggi qo'ng'iroqlar", ru: "Недавние звонки" },
  phones_masked: { uz: "Telefon raqamlar niqoblangan", ru: "Номера телефонов скрыты" },
  th_id: { uz: "ID", ru: "ID" },
  th_from: { uz: "Kimdan", ru: "Откуда" },
  th_language: { uz: "Til", ru: "Язык" },
  th_status: { uz: "Holat", ru: "Статус" },
  th_started: { uz: "Boshlangan", ru: "Начало" },
  empty_calls_title: { uz: "Hozircha qo'ng'iroqlar yo'q", ru: "Звонков пока нет" },
  empty_calls_hint: {
    uz: "Registrator qo'ng'iroq qabul qilgach bu yerda ko'rinadi.",
    ru: "Звонки появятся здесь после приёма регистратором.",
  },
  gap_title: { uz: "Backend bo'shlig'i", ru: "Пробел бэкенда" },
  gap_sub: { uz: "API hali bermaydigan ko'rsatkichlar", ru: "Метрики, которых пока нет в API" },
  gap_avg_ai_latency: { uz: "O'rtacha AI javob kechikishi", ru: "Средняя задержка ответа AI" },
  gap_avg_tts: { uz: "O'rtacha TTS birinchi qism kechikishi", ru: "Средняя задержка первого фрагмента TTS" },
  gap_emergency: { uz: "Favqulodda / xavfsizlik eskalatsiyalari soni", ru: "Число экстренных эскалаций" },
  gap_provider_errors: { uz: "STT/TTS provayder xatolari soni", ru: "Число ошибок провайдера STT/TTS" },
  gap_barge: { uz: "Barge-in soni", ru: "Число прерываний (barge-in)" },
  gap_missed: { uz: "O'tkazib yuborilgan qo'ng'iroqlar soni", ru: "Число пропущенных звонков" },
  gap_requires: { uz: "Analitika endpointi kerak", ru: "Требуется эндпоинт аналитики" },
  gap_footer: {
    uz: "Bu ko'rsatkichlar backend analitika endpointini talab qiladi. Har bir oqim metadatasida kechikish allaqachon mavjud.",
    ru: "Эти метрики требуют аналитического эндпоинта. Задержка по каждому потоку уже есть в метаданных.",
  },

  // provider readiness
  rd_title: { uz: "Tizim tayyorligi", ru: "Готовность системы" },
  rd_subtitle: {
    uz: "Faqat konfiguratsiya tekshiruvi. Kalit yoki token hech qachon ko'rsatilmaydi.",
    ru: "Только проверка конфигурации. Ключи и токены не отображаются.",
  },
  rd_redaction_label: { uz: "Redaksiya eslatmasi:", ru: "Примечание о редактировании:" },
  rd_errors: { uz: "Xatoliklar", ru: "Ошибки" },
  rd_errors_sub: {
    uz: "Bloklovchi — jonli qo'ng'iroqdan oldin hal qiling",
    ru: "Блокирующие — устраните до живого звонка",
  },
  rd_no_errors: { uz: "Bloklovchi xatoliklar yo'q.", ru: "Блокирующих ошибок нет." },
  rd_warnings: { uz: "Ogohlantirishlar", ru: "Предупреждения" },
  rd_warnings_sub: { uz: "Bloklamaydigan maslahatlar", ru: "Не блокирующие предупреждения" },
  rd_no_warnings: { uz: "Ogohlantirishlar yo'q.", ru: "Предупреждений нет." },
  rd_pipeline: { uz: "Quvur", ru: "Конвейер" },
  rd_providers: { uz: "Provayderlar", ru: "Провайдеры" },
  rd_providers_sub: {
    uz: "Twilio audio mosligi: mu-law / 8000 / container=none",
    ru: "Совместимость аудио Twilio: mu-law / 8000 / container=none",
  },
  rd_smoke_gate: { uz: "Smoke rejimi darvozasi", ru: "Шлюз Smoke-режима" },
  rd_privacy: { uz: "Maxfiylik", ru: "Приватность" },
  r_twilio_media: { uz: "Twilio media oqimlari", ru: "Медиапотоки Twilio" },
  r_streaming_stt: { uz: "Streaming STT", ru: "Потоковый STT" },
  r_streaming_tts: { uz: "Streaming TTS", ru: "Потоковый TTS" },
  r_ai_turns: { uz: "AI navbatlari", ru: "Ходы AI" },
  r_barge: { uz: "Barge-in", ru: "Прерывание (barge-in)" },
  r_latency_metrics: { uz: "Kechikish metrikalari", ru: "Метрики задержки" },
  r_dg_key_present: { uz: "Deepgram API kaliti", ru: "Ключ Deepgram API" },
  r_stt_model: { uz: "STT modeli", ru: "Модель STT" },
  r_tts_model: { uz: "TTS modeli", ru: "Модель TTS" },
  r_stt_twilio: { uz: "STT Twilio mosligi", ru: "Совместимость STT Twilio" },
  r_tts_twilio: { uz: "TTS Twilio mosligi", ru: "Совместимость TTS Twilio" },
  r_require_token: { uz: "Smoke token talab qilinadi", ru: "Требуется smoke-токен" },
  r_token_present: { uz: "Smoke token", ru: "Smoke-токен" },
  r_allowed_numbers: { uz: "Ruxsat etilgan raqamlar", ru: "Разрешённые номера" },
  r_max_duration: { uz: "Maksimal davomiylik (s)", ru: "Макс. длительность (с)" },
  r_max_turns: { uz: "Maksimal navbatlar", ru: "Макс. ходов" },
  r_redact: { uz: "Transkriptlarni yashirish (faqat metadata)", ru: "Скрытие транскриптов (только метаданные)" },
  r_no_patient: { uz: "Bemor ma'lumotisiz eslatma", ru: "Уведомление: без данных пациента" },
  rd_privacy_note: {
    uz: "Transkript yashirish faqat oqim metadatasiga taalluqli; CallSession transkript yozuvlari bu bayroq bilan yashirilmaydi. Smoke rejimida real bemor ma'lumotidan foydalanmang.",
    ru: "Скрытие транскриптов касается только метаданных потока; записи транскриптов CallSession этим флагом не скрываются. Не используйте реальные данные пациентов в smoke-режиме.",
  },
  key_present: { uz: "Mavjud", ru: "Доступен" },
  key_hidden: { uz: "Ko'rsatilmaydi", ru: "Не отображается" },

  home_card_booking: { uz: "Onlayn yozilish", ru: "Онлайн-запись" },
  home_card_booking_hint: {
    uz: "Mijozlar uchun ochiq qabulga yozilish sahifasi",
    ru: "Открытая страница записи на приём для клиентов",
  },

  // --- Public self-service booking (customer-facing) -------------------------
  book_brand: { uz: "Urologiya klinikasi", ru: "Урологическая клиника" },
  book_brand_sub: { uz: "Onlayn qabulga yozilish", ru: "Онлайн-запись на приём" },
  book_hero_title: { uz: "Qabulga onlayn yoziling", ru: "Запишитесь на приём онлайн" },
  book_hero_sub: {
    uz: "Bir necha qadamda shifokor va qulay vaqtni tanlang. So'rovingiz qabul qilinadi va klinika xodimi tasdiqlaydi.",
    ru: "Выберите врача и удобное время за несколько шагов. Заявка будет принята и подтверждена сотрудником клиники.",
  },
  book_step: { uz: "Qadam", ru: "Шаг" },
  book_step_service: { uz: "Yo'nalish", ru: "Направление" },
  book_step_doctor: { uz: "Shifokor", ru: "Врач" },
  book_step_time: { uz: "Sana va vaqt", ru: "Дата и время" },
  book_step_contact: { uz: "Ma'lumotlaringiz", ru: "Ваши данные" },
  book_step_done: { uz: "Tayyor", ru: "Готово" },
  book_choose_service: { uz: "Yo'nalishni tanlang", ru: "Выберите направление" },
  book_choose_doctor: { uz: "Shifokorni tanlang", ru: "Выберите врача" },
  book_choose_date: { uz: "Sanani tanlang", ru: "Выберите дату" },
  book_choose_time: { uz: "Bo'sh vaqtni tanlang", ru: "Выберите свободное время" },
  book_doctors_count: { uz: "shifokor", ru: "врач(ей)" },
  book_no_doctors: { uz: "Bu yo'nalishda hozircha shifokor yo'q.", ru: "По этому направлению пока нет врачей." },
  book_no_slots: {
    uz: "Tanlangan kunda bo'sh vaqt yo'q. Boshqa kunni tanlang.",
    ru: "На выбранный день нет свободного времени. Выберите другой день.",
  },
  book_no_services: {
    uz: "Hozircha onlayn yozilish uchun yo'nalishlar mavjud emas.",
    ru: "Пока нет направлений для онлайн-записи.",
  },
  book_name: { uz: "Ism familiya", ru: "Имя и фамилия" },
  book_name_ph: { uz: "Masalan: Aliyev Akmal", ru: "Например: Алиев Акмал" },
  book_phone: { uz: "Telefon raqam", ru: "Номер телефона" },
  book_phone_ph: { uz: "+998 90 123 45 67", ru: "+998 90 123 45 67" },
  book_phone_hint: { uz: "O'zbekiston raqami: +998 bilan", ru: "Номер Узбекистана: с +998" },
  book_notes: { uz: "Izoh (ixtiyoriy)", ru: "Комментарий (необязательно)" },
  book_notes_ph: { uz: "Qisqacha murojaat sababi", ru: "Кратко причина обращения" },
  book_summary: { uz: "Yozilish ma'lumotlari", ru: "Данные записи" },
  book_back: { uz: "Orqaga", ru: "Назад" },
  book_next: { uz: "Davom etish", ru: "Продолжить" },
  book_submit: { uz: "Yozilishni tasdiqlash", ru: "Подтвердить запись" },
  book_submitting: { uz: "Yuborilmoqda...", ru: "Отправка..." },
  book_success_title: { uz: "So'rovingiz qabul qilindi", ru: "Ваша заявка принята" },
  book_success_sub: {
    uz: "Klinika xodimi qisqa vaqt ichida siz bilan bog'lanib, qabulni tasdiqlaydi.",
    ru: "Сотрудник клиники свяжется с вами в ближайшее время и подтвердит приём.",
  },
  book_reference: { uz: "So'rov raqami", ru: "Номер заявки" },
  book_status_pending: { uz: "Tasdiq kutilmoqda", ru: "Ожидает подтверждения" },
  book_new_one: { uz: "Yana yozilish", ru: "Записаться снова" },
  book_required: { uz: "Iltimos, ism va telefon raqamini kiriting.", ru: "Пожалуйста, укажите имя и номер телефона." },
  // booking error codes (backend `detail`)
  book_err_invalid_phone: { uz: "Telefon raqam noto'g'ri. +998 bilan kiriting.", ru: "Неверный номер. Введите с +998." },
  book_err_invalid_name: { uz: "Ism noto'g'ri kiritildi.", ru: "Имя указано неверно." },
  book_err_slot_taken: { uz: "Bu vaqt band qilindi. Boshqa vaqtni tanlang.", ru: "Это время уже занято. Выберите другое." },
  book_err_too_many_active: {
    uz: "Sizda faol so'rovlar ko'p. Avval ularni tasdiqlatib oling.",
    ru: "У вас слишком много активных заявок. Дождитесь их подтверждения.",
  },
  book_err_doctor_unavailable: { uz: "Tanlangan shifokor mavjud emas.", ru: "Выбранный врач недоступен." },
  book_err_rate_limited: { uz: "Juda ko'p urinish. Birozdan so'ng qayta urinib ko'ring.", ru: "Слишком много попыток. Повторите позже." },
  book_err_generic: { uz: "Xatolik yuz berdi. Qayta urinib ko'ring.", ru: "Произошла ошибка. Повторите попытку." },
};

// Doctor specialty codes -> human labels (urology clinic). Falls back to the
// raw value (title-cased) for unknown specialties.
const SPECIALTY: Record<string, Entry> = {
  urolog: { uz: "Urolog", ru: "Уролог" },
  urologist: { uz: "Urolog", ru: "Уролог" },
  androlog: { uz: "Androlog", ru: "Андролог" },
  nefrolog: { uz: "Nefrolog", ru: "Нефролог" },
  uzi: { uz: "UZI diagnostikasi", ru: "УЗИ-диагностика" },
};

// --- backend enum/code -> display translation (rendered, never raw English) --
const STATUS: Record<string, Entry> = {
  ready: { uz: "Tayyor", ru: "Готово" },
  not_ready: { uz: "Tayyor emas", ru: "Не готово" },
  ok: { uz: "Tayyor", ru: "Готово" },
  active: { uz: "Faol", ru: "Активный" },
  online: { uz: "Onlayn", ru: "Онлайн" },
  completed: { uz: "Bajarilgan", ru: "Завершён" },
  confirmed: { uz: "Tasdiqlangan", ru: "Подтверждён" },
  pending: { uz: "Kutilmoqda", ru: "Ожидает" },
  in_progress: { uz: "Jarayonda", ru: "В процессе" },
  callback_required: { uz: "Qayta qo'ng'iroq", ru: "Обратный звонок" },
  needs_operator: { uz: "Operator kerak", ru: "Нужен оператор" },
  transfer: { uz: "Uzatish", ru: "Передача" },
  transferred: { uz: "Uzatildi", ru: "Передан" },
  new: { uz: "Yangi", ru: "Новый" },
  allow: { uz: "Ruxsat", ru: "Разрешено" },
  error: { uz: "Xatolik", ru: "Ошибка" },
  failed: { uz: "Muvaffaqiyatsiz", ru: "Неудачно" },
  emergency: { uz: "Favqulodda", ru: "Экстренный" },
  degraded: { uz: "Buzilgan", ru: "Деградировал" },
  cancelled: { uz: "Bekor qilingan", ru: "Отменён" },
  missed: { uz: "O'tkazib yuborilgan", ru: "Пропущен" },
  assigned: { uz: "Tayinlangan", ru: "Назначен" },
  // callback reasons
  operator_request: { uz: "Operator so'rovi", ru: "Запрос оператора" },
  medical_question: { uz: "Tibbiy savol", ru: "Медицинский вопрос" },
  complaint: { uz: "Shikoyat", ru: "Жалоба" },
  unclear: { uz: "Noaniq", ru: "Неясно" },
  low_confidence: { uz: "Past ishonch", ru: "Низкая уверенность" },
  // priorities
  normal: { uz: "Oddiy", ru: "Обычный" },
  high: { uz: "Yuqori", ru: "Высокий" },
  urgent: { uz: "Shoshilinch", ru: "Срочный" },
  low: { uz: "Past", ru: "Низкий" },
  // telephony
  received: { uz: "Qabul qilindi", ru: "Получен" },
  processed: { uz: "Qayta ishlandi", ru: "Обработан" },
  inbound: { uz: "Kiruvchi", ru: "Входящий" },
  outbound: { uz: "Chiquvchi", ru: "Исходящий" },
  // audio kinds + transcript roles
  user_audio: { uz: "Mijoz audiosi", ru: "Аудио клиента" },
  ai_tts: { uz: "AI ovozi", ru: "Голос AI" },
  full_call: { uz: "To'liq qo'ng'iroq", ru: "Полный звонок" },
  system: { uz: "Tizim", ru: "Система" },
  user: { uz: "Mijoz", ru: "Клиент" },
  assistant: { uz: "AI", ru: "AI" },
  // appointment statuses (M2)
  arrived: { uz: "Keldi", ru: "Прибыл" },
  no_show: { uz: "Kelmadi", ru: "Не явился" },
  operator_required: { uz: "Operator kerak", ru: "Нужен оператор" },
  // appointment sources (M2)
  ai_call: { uz: "AI qo'ng'irog'i", ru: "AI звонок" },
  operator: { uz: "Operator", ru: "Оператор" },
  manual: { uz: "Qo'lda", ru: "Вручную" },
  web: { uz: "Onlayn", ru: "Онлайн" },
};

// Knowledge-base category codes -> human labels (urology clinic).
const CATEGORY: Record<string, Entry> = {
  clinic_info: { uz: "Klinika ma'lumotlari", ru: "Информация о клинике" },
  branches: { uz: "Filiallar", ru: "Филиалы" },
  services_prices: { uz: "Xizmatlar va narxlar", ru: "Услуги и цены" },
  urology_services_prices: { uz: "Urologiya xizmatlari va narxlari", ru: "Урологические услуги и цены" },
  doctors: { uz: "Shifokorlar", ru: "Врачи" },
  doctor_schedule: { uz: "Shifokorlar jadvali", ru: "Расписание врачей" },
  appointment_rules: { uz: "Qabul qoidalari", ru: "Правила записи" },
  faq: { uz: "Savol-javob", ru: "Вопросы и ответы" },
  preparation_instructions: { uz: "Tayyorgarlik ko'rsatmalari", ru: "Инструкции по подготовке" },
  operator_rules: { uz: "Operator qoidalari", ru: "Правила оператора" },
  safety_rules: { uz: "Xavfsizlik qoidalari", ru: "Правила безопасности" },
  emergency_policy: { uz: "Favqulodda holat siyosati", ru: "Политика экстренных ситуаций" },
};

interface Ctx {
  locale: Locale;
  setLocale: (l: Locale) => void;
}

const LanguageContext = createContext<Ctx>({ locale: "uz", setLocale: () => {} });

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("uz");

  useEffect(() => {
    const saved = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (saved === "uz" || saved === "ru") setLocaleState(saved);
  }, []);

  function setLocale(l: Locale) {
    setLocaleState(l);
    try {
      window.localStorage.setItem(STORAGE_KEY, l);
    } catch {
      // ignore persistence failure
    }
  }

  return <LanguageContext.Provider value={{ locale, setLocale }}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const { locale, setLocale } = useContext(LanguageContext);
  function t(key: string): string {
    const e = DICT[key];
    return e ? e[locale] : key;
  }
  function tStatus(code?: string | null): string {
    const key = (code || "").toLowerCase();
    const e = STATUS[key];
    return e ? e[locale] : code || "-";
  }
  function tCat(code?: string | null): string {
    const key = (code || "").toLowerCase();
    const e = CATEGORY[key];
    return e ? e[locale] : code || "-";
  }
  function tSpec(code?: string | null): string {
    const raw = (code || "").trim();
    const e = SPECIALTY[raw.toLowerCase()];
    if (e) return e[locale];
    return raw ? raw.charAt(0).toUpperCase() + raw.slice(1) : "-";
  }
  return { locale, setLocale, t, tStatus, tCat, tSpec };
}

export function LanguageSwitcher({ className = "" }: { className?: string }) {
  const { locale, setLocale } = useLanguage();
  return (
    <div className={`inline-flex overflow-hidden rounded border border-slate-300 text-xs ${className}`}>
      {LOCALES.map((l) => (
        <button
          key={l.value}
          onClick={() => setLocale(l.value)}
          className={`px-2 py-1 ${
            locale === l.value ? "bg-blue-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"
          }`}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
