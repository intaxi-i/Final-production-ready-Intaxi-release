import asyncio
import logging
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.database.models import async_main
from app.handlers.live_city_hotfix import router as live_city_hotfix_router
from app.handlers.profile_hotfix import router as profile_hotfix_router
from app.handlers.start import router as start_router
from app.handlers.profile import router as profile_router
from app.handlers.order import router as order_router
from app.handlers.admin import router as admin_router
from app.handlers.driver_reg import router as driver_router
from app.miniapp_routes import home_url
from app.runtime_hotfixes import apply_runtime_hotfixes

load_dotenv()
apply_runtime_hotfixes()


async def main():
    await async_main()

    bot = Bot(
        token=os.getenv('BOT_TOKEN'),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(admin_router)
    dp.include_router(driver_router)
    dp.include_router(live_city_hotfix_router)
    dp.include_router(start_router)
    dp.include_router(profile_hotfix_router)
    dp.include_router(profile_router)
    dp.include_router(order_router)

    print("Intaxi Bot with Admin Panel is RUNNING! 🚀")

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await bot.set_chat_menu_button(
            menu_button=types.MenuButtonWebApp(
                text="Open Intaxi",
                web_app=types.WebAppInfo(url=home_url("chat-menu")),
            )
        )
    except Exception:
        pass
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")
