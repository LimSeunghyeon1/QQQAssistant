from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import parse_qs, urlparse

from app.services.taobao_client import TaobaoClient


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
    """Scraper that delegates to the official Taobao TOP API client."""

    def __init__(self, client: Optional[TaobaoClient] = None) -> None:
        # Delay client initialization until it's actually needed so that
        # local/test environments without TAOBAO credentials can fall back to
        # a deterministic dummy product instead of raising during import.
        self.client = client

    def _dummy_product(self, url: str, option_name: str = "Default Option") -> ScrapedProduct:
        return ScrapedProduct(
            source_url=url,
            source_site="TAOBAO",
            title="Dummy Taobao Product",
            price=0,
            currency="CNY",
            image_urls=[],
            options=[
                ScrapedOption(
                    option_key="default",
                    raw_name=option_name,
                    raw_price_diff=0,
                )
            ],
        )

    async def fetch_product(self, url: str) -> ScrapedProduct:
        num_iid = self._extract_num_iid(url)
        if not num_iid:
            return self._dummy_product(url)

        try:
            client = self.client or TaobaoClient()
            self.client = client
        except ValueError:
            return self._dummy_product(url)

        try:
            data = await asyncio.to_thread(client.get_item_detail, num_iid)
        except Exception:
            return self._dummy_product(url)
        item = data.get("item_get_response", {}).get("item", {})

        title = item.get("title", "")
        price = float(item.get("price", 0))
        pic_url = item.get("pic_url", "")
        image_urls = [pic_url] if pic_url else []

        # SKU/option parsing would depend on the exact API fields returned.
        options: List[ScrapedOption] = []

        if not title:
            return self._dummy_product(url)

        if not options:
            options.append(
                ScrapedOption(option_key="default", raw_name="Default Option", raw_price_diff=0)
            )

        return ScrapedProduct(
            source_url=f"https://item.taobao.com/item.htm?id={num_iid}",
            source_site="TAOBAO",
            title=title,
            price=price,
            currency="CNY",
            image_urls=image_urls,
            options=options,
        )

    def _extract_num_iid(self, url: str) -> Optional[str]:
        """Extract ``num_iid`` from common Taobao item URLs or direct IDs."""

        if re.fullmatch(r"\d+", url):
            return url

        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        num_iid = query_params.get("id")
        if num_iid:
            return num_iid[0]

        # Fallback for URLs that might embed the ID in the path.
        match = re.search(r"id=(\d+)", url)
        if match:
            return match.group(1)

        return None
