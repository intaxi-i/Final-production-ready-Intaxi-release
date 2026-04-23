import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.database.models import async_main
from app.handlers.start import router as start_router
from app.handlers.profile import router as profile_router
from app.handlers.order import router as order_router
from app.handlers.admin import router as admin_router
from app.handlers.driver_reg import router as driver_router

load_dotenv()

async def main():
    await async_main()
    
    bot = Bot(
        token=os.getenv('BOT_TOKEN'), 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Важно: admin_router лучше ставить выше, чтобы перехватывать команды админа
    dp.include_router(admin_router)
    dp.include_router(driver_router)
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(order_router)

    print("Intaxi Bot with Admin Panel is RUNNING! 🚀")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")