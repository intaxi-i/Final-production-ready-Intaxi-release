from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

import app.keyboards as kb
from app.hotfix_menu import home_webapp_menu

ADMIN_PANEL_LABELS = {
    'ru': '🛡 Админ-панель',
    'uz': '🛡 Admin paneli',
    'en': '🛡 Admin panel',
    'ar': '🛡 لوحة الإدارة',
}


def install_main_menu_consistency() -> None:
    if getattr(kb, '_intaxi_main_menu_consistency_installed', False):
        return

    original_main_menu = kb.main_menu

    def unified_main_menu(lang, user_id=None, as_user=False, is_driver_mode: bool = False, is_admin: bool | None = None):
        admin_flag = kb._db_admin_flag(user_id) if is_admin is None else bool(is_admin)
        if admin_flag and not as_user:
            return kb.admin_main_kb(lang, user_id=user_id)

        markup = home_webapp_menu(lang, is_driver_mode=is_driver_mode)

        if admin_flag and as_user:
            rows = [list(row) for row in markup.keyboard]
            rows.append([KeyboardButton(text=ADMIN_PANEL_LABELS.get(lang, ADMIN_PANEL_LABELS['ru']))])
            return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

        return markup

    kb._intaxi_original_main_menu = original_main_menu
    kb.main_menu = unified_main_menu
    kb._intaxi_main_menu_consistency_installed = True
