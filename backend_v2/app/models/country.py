from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin


class Country(TimestampMixin, Base):
    __tablename__ = "countries_v2"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(128), nullable=False)
    name_local: Mapped[str] = mapped_column(String(128), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    map_provider: Mapped[str] = mapped_column(String(32), default="mixed", nullable=False)
    default_language: Mapped[str] = mapped_column(String(8), default="ru", nullable=False)

    cities = relationship("City", back_populates="country")


class City(TimestampMixin, Base):
    __tablename__ = "cities_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(String(8), ForeignKey("countries_v2.code"), index=True)
    region_name: Mapped[str | None] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(128), nullable=False)
    name_local: Mapped[str] = mapped_column(String(128), nullable=False)
    lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    country = relationship("Country", back_populates="cities")
