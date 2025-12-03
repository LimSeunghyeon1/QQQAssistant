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
    detail_image_urls: List[str]
    options: List[ScrapedOption]


class TaobaoScraper:
    """Scraper that delegates to the official Taobao TOP API client."""

    def __init__(self, client: Optional[TaobaoClient] = None) -> None:
        try:
            self.client = client or TaobaoClient()
        except Exception:
            self.client = None

    async def fetch_product(self, url: str) -> ScrapedProduct:
        num_iid = self._extract_num_iid(url)
        if not num_iid or not self.client:
            return self._fallback_product(url)

        try:
            data = await asyncio.to_thread(self.client.get_item_detail, num_iid)
            item = data.get("item_get_response", {}).get("item", {})
            title = item.get("title", "")
            price = float(item.get("price", 0))
            pic_url = item.get("pic_url", "")
            image_urls = [pic_url] if pic_url else []
            detail_image_urls: List[str] = []
        except Exception:
            return self._fallback_product(url)

        options: List[ScrapedOption] = []
        for sku in item.get("skus", {}).get("sku", []) or []:
            option = ScrapedOption(
                option_key=str(sku.get("properties", "default")),
                raw_name=sku.get("sku_name", sku.get("properties_name", "Default")),
                raw_price_diff=float(sku.get("price", 0)) - price if price else None,
            )
            options.append(option)

        if not options:
            options.append(ScrapedOption(option_key="default", raw_name="기본", raw_price_diff=0))

        return ScrapedProduct(
            source_url=f"https://item.taobao.com/item.htm?id={num_iid}",
            source_site="TAOBAO",
            title=title or "Taobao Item",
            price=price,
            currency="CNY",
            image_urls=image_urls,
            detail_image_urls=detail_image_urls,
            options=options,
        )

    def _fallback_product(self, url: str) -> ScrapedProduct:
        default_option = ScrapedOption(option_key="default", raw_name="Default")

        return ScrapedProduct(
            source_url=url,
            source_site="TAOBAO",
            title="Dummy Taobao Product",
            price=0.0,
            currency="CNY",
            image_urls=[],
            detail_image_urls=[],
            options=[default_option],
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

        trailing_digits = re.search(r"(\d+)(?!.*\d)", parsed.path)
        if trailing_digits:
            return trailing_digits.group(1)

        return None
