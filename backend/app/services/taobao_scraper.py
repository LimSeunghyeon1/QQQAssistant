from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ScrapedOption:
    option_key: str
    raw_name: str
    raw_price_diff: Optional[float] = None


@dataclass
class ScrapedProduct:
    source_url: str
    source_site: str
    title: str
    price: float
    currency: str
    image_urls: List[str]
    options: List[ScrapedOption]


class TaobaoScraper:
    """Placeholder scraper for Taobao products."""

    async def fetch_product(self, url: str) -> ScrapedProduct:
        # TODO: replace with a real scraper or OpenAPI client
        return ScrapedProduct(
            source_url=url,
            source_site="TAOBAO",
            title="Dummy Taobao Product",
            price=100.0,
            currency="CNY",
            image_urls=[],
            options=[
                ScrapedOption(
                    option_key="default",
                    raw_name="Default Option",
                    raw_price_diff=0,
                )
            ],
        )
