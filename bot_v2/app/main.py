from __future__ import annotations

import asyncio
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.notifications import current_trip_url

router = Router()

MINIAPP_BASE_URL = os.getenv("INTAXI_MINIAPP_BASE_URL", "https://app.intaxi.best")


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Intaxi V2 готовит поездки в Mini App. Откройте приложение, чтобы создать заказ, выйти online или посмотреть текущую поездку."
    )


@router.message(lambda message: message.text == "/trip")
async def current_trip(message: Message) -> None:
    await message.answer(f"Текущая поездка: {current_trip_url(MINIAPP_BASE_URL, 0)}")


async def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is required")
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
