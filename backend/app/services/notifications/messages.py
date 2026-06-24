"""Compose patient-facing appointment SMS text (Uzbek / Russian).

Kept provider-agnostic: returns plain text the channel layer sends as-is.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.core.config import settings


def _fmt_when(dt: Optional[datetime]) -> str:
    if dt is None:
        return "-"
    return dt.strftime("%d.%m.%Y %H:%M")


def appointment_sms_text(
    *,
    kind: str,
    patient_name: Optional[str],
    scheduled_at: Optional[datetime],
    doctor_name: Optional[str] = None,
    locale: str = "uz",
    clinic: Optional[str] = None,
) -> str:
    clinic = clinic or settings.clinic_display_name
    name = (patient_name or "").strip()
    when = _fmt_when(scheduled_at)
    doc = (doctor_name or "").strip()

    if locale == "ru":
        hello = f"Уважаемый(ая) {name}, " if name else ""
        if kind == "booking_received":
            return f"{hello}ваша заявка на приём получена. Дата: {when}. Скоро подтвердим. {clinic}"
        if kind == "confirmed":
            doc_part = f", врач: {doc}" if doc else ""
            return f"{hello}ваш приём ПОДТВЕРЖДЁН. Дата: {when}{doc_part}. {clinic}"
        if kind == "cancelled":
            return f"{hello}ваш приём на {when} отменён. По вопросам свяжитесь с нами. {clinic}"
        if kind == "reminder":
            return f"{hello}напоминаем о приёме: {when}. {clinic}"
        return f"{hello}{when}. {clinic}"

    # default: Uzbek
    hello = f"Hurmatli {name}, " if name else ""
    if kind == "booking_received":
        return f"{hello}qabulga yozilish so'rovingiz qabul qilindi. Sana: {when}. Tez orada tasdiqlaymiz. {clinic}"
    if kind == "confirmed":
        doc_part = f", shifokor: {doc}" if doc else ""
        return f"{hello}qabulingiz TASDIQLANDI. Sana: {when}{doc_part}. {clinic}"
    if kind == "cancelled":
        return f"{hello}{when} qabulingiz bekor qilindi. Savollar uchun biz bilan bog'laning. {clinic}"
    if kind == "reminder":
        return f"{hello}qabulni eslatamiz: {when}. {clinic}"
    return f"{hello}{when}. {clinic}"
