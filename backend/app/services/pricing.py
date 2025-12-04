from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.config import settings


@dataclass
class PricingContext:
    """Configuration driving sale price calculations."""

    exchange_rate: float = settings.exchange_rate
    default_margin: float = settings.default_margin
    vat_rate: float = settings.vat_rate
    default_delivery: float = settings.default_delivery


class PricingService:
    """Calculate sale prices based on cost, shipping, margin, and VAT.

    The defaults are sourced from environment variables, but each call can
    override the values when channel-specific rules are needed.
    """

    def __init__(self, context: Optional[PricingContext] = None) -> None:
        self.context = context or PricingContext()

    def calculate_sale_price(
        self,
        raw_price_cny: float,
        option_price_diff_cny: float = 0,
        *,
        shipping_fee: float | None = None,
        margin_rate: float | None = None,
        vat_rate: float | None = None,
        exchange_rate: float | None = None,
    ) -> float:
        ctx = self.context
        rate = exchange_rate if exchange_rate is not None else ctx.exchange_rate
        margin = margin_rate if margin_rate is not None else ctx.default_margin
        vat = vat_rate if vat_rate is not None else ctx.vat_rate
        delivery_fee = shipping_fee if shipping_fee is not None else ctx.default_delivery

        base_cost_krw = (float(raw_price_cny) + float(option_price_diff_cny)) * rate
        subtotal = base_cost_krw + float(delivery_fee)
        with_margin = subtotal * (1 + float(margin) / 100)
        final_price = with_margin * (1 + float(vat) / 100)
        return round(final_price, 2)
