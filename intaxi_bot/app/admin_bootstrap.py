from __future__ import annotations

import os
import sqlite3
from typing import Iterable

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

ADMIN_LABELS = {
    'dashboard': '📊 Dashboard',
    'users': '👥 Пользователи',
    'drivers': '🚕 Водители',
    'finance': '💳 Финансы',
    'orders': '🧾 Заказы',
    'moderation': '🛎 Модерация',
    'broadcast': '📢 Рассылка',
    'payments': '💳 Пополнения',
    'lookup': '🔎 Пользователь по ID',
    'feedback': '💬 Отзывы',
    'complaints': '⚠️ Жалобы',
    'user_mode': '👤 Режим пользователя',
    'admins': '🛡 Админы',
}

ROLE_PERMISSIONS = {
    'superadmin': ['dashboard', 'users', 'drivers', 'finance', 'orders', 'moderation', 'payments', 'lookup', 'feedback', 'complaints', 'broadcast', 'admins'],
    'admin': ['dashboard', 'users', 'drivers', 'orders', 'moderation', 'payments', 'lookup', 'feedback', 'complaints', 'broadcast'],
    'moderator': ['dashboard', 'drivers', 'moderation', 'feedback', 'complaints', 'broadcast'],
    'finance': ['dashboard', 'finance', 'payments', 'lookup', 'broadcast'],
}


def _db_path() -> str:
    db_url = os.getenv('DATABASE_URL')
    db_path = os.getenv('DB_PATH') or 'db.sqlite3'
    if db_url and db_url.startswith('sqlite'):
        return db_url.replace('sqlite+aiosqlite:///', '').replace('sqlite:///', '')
    return db_path


def _db_admin_role(user_id: int | None) -> str | None:
    if not user_id:
        return None
    try:
        with sqlite3.connect(_db_path()) as conn:
            row = conn.execute('SELECT role FROM admin_roles WHERE tg_id=? AND is_active=1 ORDER BY id DESC LIMIT 1', (user_id,)).fetchone()
            return row[0] if row else None
    except Exception:
        return None


def _rows(keys: Iterable[str]) -> list[list[KeyboardButton]]:
    rows: list[list[KeyboardButton]] = []
    current: list[KeyboardButton] = []
    for key in keys:
        label = ADMIN_LABELS.get(key)
        if not label:
            continue
        current.append(KeyboardButton(text=label))
        if len(current) == 2:
            rows.append(current)
            current = []
    if current:
        rows.append(current)
    rows.append([KeyboardButton(text=ADMIN_LABELS['user_mode'])])
    return rows


def patched_admin_main_kb(lang: str = 'ru', user_id: int | None = None):
    role = _db_admin_role(user_id)
    permissions = ROLE_PERMISSIONS.get(role, ['dashboard'])
    return ReplyKeyboardMarkup(keyboard=_rows(permissions), resize_keyboard=True)


def apply_admin_menu_config() -> None:
    try:
        import app.keyboards as kb
        kb.admin_main_kb = patched_admin_main_kb
    except Exception:
        pass
    try:
        import intaxi_bot.app.keyboards as kb2
        kb2.admin_main_kb = patched_admin_main_kb
    except Exception:
        pass
