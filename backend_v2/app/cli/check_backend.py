from __future__ import annotations

from app.core.database import Base
from app import models  # noqa: F401
from app.main import app


def main() -> None:
    print(app.title)
    print(len(Base.metadata.tables))
    print(sorted(Base.metadata.tables.keys()))


if __name__ == "__main__":
    main()
