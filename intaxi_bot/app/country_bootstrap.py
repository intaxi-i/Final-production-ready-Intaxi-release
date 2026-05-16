from __future__ import annotations

import importlib
from copy import deepcopy

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.country_config import DEFAULT_TARIFFS, country_code_from_address
from app.strings import MESSAGES

COUNTRY_LABELS = {
    'ru': {'kz': 'Казахстан'},
    'uz': {'kz': 'Qozog‘iston'},
    'en': {'kz': 'Kazakhstan'},
    'ar': {'kz': 'كازاخستان'},
}

KZ_CITIES = {
    'ru': ['Алматы', 'Астана', 'Шымкент', 'Караганда', 'Актобе', 'Тараз', 'Павлодар', 'Усть-Каменогорск', 'Семей', 'Костанай', 'Кызылорда', 'Атырау'],
    'uz': ['Olmaota', 'Astana', 'Shymkent', 'Qarag‘anda', 'Aqtobe', 'Taraz', 'Pavlodar', 'Oskemen', 'Semey', 'Qo‘stanay', 'Qizilo‘rda', 'Atirau'],
    'en': ['Almaty', 'Astana', 'Shymkent', 'Karaganda', 'Aktobe', 'Taraz', 'Pavlodar', 'Oskemen', 'Semey', 'Kostanay', 'Kyzylorda', 'Atyrau'],
    'ar': ['ألماتي', 'أستانا', 'شيمكنت', 'كاراغاندا', 'أكتوبه', 'تاراز', 'بافلودار', 'أوسكمان', 'سيمي', 'كوستاناي', 'قيزيلوردا', 'أتيراو'],
}

KZ_MODELS = {
    'Toyota': ['Camry', 'Corolla', 'RAV4', 'Land Cruiser', 'Hiace'],
    'Hyundai': ['Accent', 'Elantra', 'Sonata', 'Tucson', 'Staria'],
    'Kia': ['Rio', 'Cerato', 'K5', 'Sportage', 'Carnival'],
    'Chevrolet': ['Cobalt', 'Nexia', 'Lacetti', 'Malibu'],
    'Volkswagen': ['Polo', 'Passat', 'Caddy', 'Transporter'],
    'Renault': ['Logan', 'Duster', 'Kaptur'],
}

_BOOTSTRAP_APPLIED = False


def _copy_models() -> dict[str, list[str]]:
    return deepcopy(KZ_MODELS)


def _patch_messages() -> None:
    for module_name in ('app.strings', 'intaxi_bot.app.strings'):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        messages = getattr(module, 'MESSAGES', None)
        if not isinstance(messages, dict):
            continue
        for lang, pack in messages.items():
            if not isinstance(pack, dict):
                continue
            country_label = COUNTRY_LABELS.get(lang, COUNTRY_LABELS['ru'])['kz']
            pack.setdefault('countries', {})['kz'] = country_label
            pack.setdefault('cities', {})['kz'] = list(KZ_CITIES.get(lang, KZ_CITIES['ru']))
            pack.setdefault('currencies', {})['kz'] = 'KZT'
            pack.setdefault('models', {})['kz'] = _copy_models()


def _country_keyboard(lang: str, prefix: str):
    builder = InlineKeyboardBuilder()
    pack = MESSAGES.get(lang, MESSAGES['ru'])
    for country_code, label in pack.get('countries', {}).items():
        builder.button(text=label, callback_data=f'{prefix}{country_code}')
    return builder.adjust(1).as_markup()


def _patch_legacy_order_keyboards() -> None:
    for module_name in ('app.handlers.order', 'intaxi_bot.app.handlers.order'):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        setattr(module, '_country_keyboard', _country_keyboard)


def _patch_tariffs() -> None:
    for module_name in ('app.database.requests', 'intaxi_bot.app.database.requests'):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        default_tariffs = getattr(module, 'DEFAULT_TARIFFS', None)
        if isinstance(default_tariffs, dict):
            for country, tariff in DEFAULT_TARIFFS.items():
                default_tariffs.setdefault(country, tariff)


def _patch_profile_geo() -> None:
    for module_name in ('app.handlers.profile', 'intaxi_bot.app.handlers.profile'):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        setattr(module, '_country_code_from_address', country_code_from_address)


def apply_country_config() -> None:
    global _BOOTSTRAP_APPLIED
    _patch_messages()
    _patch_tariffs()
    _patch_profile_geo()
    _patch_legacy_order_keyboards()
    _BOOTSTRAP_APPLIED = True
