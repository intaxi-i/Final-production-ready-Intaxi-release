from __future__ import annotations

import importlib

from app.country_config import DEFAULT_TARIFFS, country_code_from_address

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
            pack.setdefault('cities', {})['kz'] = KZ_CITIES.get(lang, KZ_CITIES['ru'])
            pack.setdefault('currencies', {})['kz'] = 'KZT'
            pack.setdefault('models', {})['kz'] = KZ_MODELS


def apply_country_config() -> None:
    _patch_messages()

    for module_name in ('app.database.requests', 'intaxi_bot.app.database.requests'):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        default_tariffs = getattr(module, 'DEFAULT_TARIFFS', None)
        if isinstance(default_tariffs, dict):
            for country, tariff in DEFAULT_TARIFFS.items():
                default_tariffs.setdefault(country, tariff)

    for module_name in ('app.handlers.profile', 'intaxi_bot.app.handlers.profile'):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        setattr(module, '_country_code_from_address', country_code_from_address)
