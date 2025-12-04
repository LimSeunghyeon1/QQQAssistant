from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PricingInputs:
    base_price: float
    exchange_rate: float
    margin_rate: float = 0.0
    shipping_fee: float = 0.0
    vat_rate: float = 0.1
    include_vat: bool = False


class PricingService:
    """Utility to calculate a sale price from cost components."""

    def calculate_sale_price(self, inputs: PricingInputs) -> float:
        """
        Compute the final sale price in KRW.

        Steps:
        1. Convert the base price with the exchange rate.
        2. Add shipping to build the landed cost.
        3. Apply margin on top of the landed cost.
        4. Optionally apply VAT.
        """

        cost_krw = inputs.base_price * inputs.exchange_rate
        landed_cost = cost_krw + inputs.shipping_fee
        with_margin = landed_cost * (1 + inputs.margin_rate)
        if inputs.include_vat:
            with_margin *= 1 + inputs.vat_rate
        return round(with_margin / 10) * 10
