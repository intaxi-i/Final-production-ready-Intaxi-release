from __future__ import annotations

from pydantic import BaseModel, Field


class DonationPaymentSettingCreate(BaseModel):
    method_type: str = Field(min_length=2, max_length=32)
    title: str = Field(min_length=1, max_length=128)
    country_code: str | None = None
    currency: str | None = None
    card_number: str | None = None
    card_holder_name: str | None = None
    bank_name: str | None = None
    digital_asset_network: str | None = None
    digital_asset_address: str | None = None
    instructions: str | None = None
    extra_json: dict | None = None
    sort_order: int = 100
    is_active: bool = True


class DonationPaymentSettingUpdate(BaseModel):
    title: str | None = None
    country_code: str | None = None
    currency: str | None = None
    card_number: str | None = None
    card_holder_name: str | None = None
    bank_name: str | None = None
    digital_asset_network: str | None = None
    digital_asset_address: str | None = None
    instructions: str | None = None
    extra_json: dict | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class DonationPaymentSettingRead(BaseModel):
    id: int
    method_type: str
    title: str
    country_code: str | None = None
    currency: str | None = None
    card_number_masked: str | None = None
    card_holder_name: str | None = None
    bank_name: str | None = None
    digital_asset_network: str | None = None
    digital_asset_address_preview: str | None = None
    instructions: str | None = None
    extra_json: dict | None = None
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}
