# -*- coding: ascii -*-
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class InvoiceItem:
    description: str
    unit: str
    quantity: Decimal
    unit_price_with_taxes: Decimal
    amount: Decimal
    pis_cofins: Decimal
    icms_tax_base: Decimal
    icms_rate: Decimal
    icms_amount: Decimal
    unit_rate: Decimal


@dataclass(frozen=True)
class MeterItem:
    meter_number: str
    segment_time: str
    reading_date_1: str
    reading_1: Decimal
    reading_date_2: str
    reading_2: Decimal
    multiplier_factor: Decimal
    consumption_kwh: Decimal
    number_of_days: int


@dataclass(frozen=True)
class TaxItem:
    tax_name: str
    base_calc: Decimal
    rate: Decimal
    amount: Decimal


@dataclass(frozen=True)
class TaxInfo:
    invoice_number: str
    invoice_issue_date: str
    access_key: str
    cfop: str
    presentation_date: str
    tax_items: list[TaxItem]


@dataclass(frozen=True)
class CreditInfo:
    injected_hfp_kwh: float
    used_kwh: float
    updated_kwh: float
    expiring_kwh: float


@dataclass(frozen=True)
class ReadingDates:
    previous_reading: str
    current_reading: str
    reading_days: int
    next_reading: str


@dataclass(frozen=True)
class TariffFlagPeriod:
    flag: str
    start_date: str
    end_date: str


@dataclass(frozen=True)
class Invoice:
    invoice_items: list[InvoiceItem]
    meter_items: list[MeterItem]
    classification_consumer_unit: str
    supply_type: str
    installation_number: str
    customer_number: str
    customer_name: str
    tax_number: str
    lighting_responsible: str
    billing_period: str
    due_date: str
    amount_due: Decimal
    reading_dates: ReadingDates
    tax_info: TaxInfo
    important_message: str
    tariff_flag_periods: list[TariffFlagPeriod]
    credit_info: CreditInfo
