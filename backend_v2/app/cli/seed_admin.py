from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.user import User


async def seed_admin(*, tg_id: int | None, phone: str | None, full_name: str) -> None:
    if tg_id is None and not phone:
        raise SystemExit("Either --tg-id or --phone is required")

    async with AsyncSessionLocal() as session:
        user = None
        if tg_id is not None:
            user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user is None and phone:
            user = await session.scalar(select(User).where(User.phone == phone))
        if user is None:
            user = User(
                tg_id=tg_id,
                phone=phone,
                full_name=full_name,
                language="ru",
                active_role="admin",
                is_adult_confirmed=True,
            )
            session.add(user)
            await session.flush()
        else:
            user.full_name = full_name or user.full_name
            if tg_id is not None:
                user.tg_id = tg_id
            if phone:
                user.phone = phone
            user.active_role = "admin"
            user.is_blocked = False
        await session.commit()
        print(f"admin_ready id={user.id} tg_id={user.tg_id} phone={user.phone}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or promote an Intaxi V2 admin user")
    parser.add_argument("--tg-id", type=int, default=None)
    parser.add_argument("--phone", type=str, default=None)
    parser.add_argument("--full-name", type=str, default="Intaxi Admin")
    args = parser.parse_args()
    asyncio.run(seed_admin(tg_id=args.tg_id, phone=args.phone, full_name=args.full_name))


if __name__ == "__main__":
    main()
