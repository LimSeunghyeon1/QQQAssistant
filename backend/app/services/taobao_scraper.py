from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
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
    detail_image_urls: List[str] = field(default_factory=list)
    options: List[ScrapedOption] = field(default_factory=list)


class ScrapeFailed(Exception):
    """Raised when scraping a product from Taobao fails."""


class TaobaoScraper:
    """Scraper that delegates to the official Taobao TOP API client."""

    def __init__(
        self,
        client: Optional[TaobaoClient] = None,
        *,
        source_site: str = "TAOBAO",
        item_source_market: str | None = None,
    ) -> None:
        self.source_site = source_site.upper()
        self.item_source_market = item_source_market
        try:
            self.client = client or TaobaoClient()
        except Exception:
            self.client = None

    async def fetch_product(self, url: str) -> ScrapedProduct:
        num_iid = self._extract_num_iid(url)
        if not num_iid:
            raise ScrapeFailed("상품 ID를 URL에서 추출할 수 없습니다.")
        if not self.client:
            raise ScrapeFailed("Taobao 클라이언트를 초기화하지 못했습니다.")

        try:
            data = await asyncio.to_thread(
                self.client.get_item_detail,
                num_iid,
                item_source_market=self.item_source_market,
            )
            item = data.get("data") or data.get("item_get_response", {}).get("item", {})
            title = item.get("title", "")
            price = self._safe_float(item.get("promotion_price") or item.get("price"), 0)

            image_urls = self._normalize_image_list(item.get("pic_urls"))
            if not image_urls:
                pic_url = item.get("pic_url")
                if pic_url:
                    image_urls.append(str(pic_url))
            if not image_urls:
                image_urls.extend(self._extract_sku_images(item.get("sku_list") or []))

            detail_image_urls = self._extract_detail_images(item)
        except Exception as exc:
            raise ScrapeFailed("상품 정보를 불러오는 중 오류가 발생했습니다.") from exc

        options: List[ScrapedOption] = []
        skus = item.get("sku_list") or item.get("skus", {}).get("sku", []) or []
        for sku in skus:
            sku_price = self._safe_float(
                sku.get("promotion_price") or sku.get("price"), None
            )
            option = ScrapedOption(
                option_key=str(
                    sku.get("sku_id")
                    or sku.get("prop_path")
                    or sku.get("properties", "default")
                ),
                raw_name=(
                    sku.get("sku_name")
                    or sku.get("prop_text")
                    or sku.get("properties_name")
                    or sku.get("properties")
                    or "Default"
                ),
                raw_price_diff=sku_price - price if price and sku_price is not None else None,
            )
            options.append(option)

        if not options:
            options.append(ScrapedOption(option_key="default", raw_name="기본", raw_price_diff=0))

        return ScrapedProduct(
            source_url=f"https://item.taobao.com/item.htm?id={num_iid}",
            source_site=self.source_site,
            title=title or "Taobao Item",
            price=price,
            currency="CNY",
            image_urls=image_urls,
            detail_image_urls=detail_image_urls,
            options=options,
        )

    def _normalize_image_list(self, images: Optional[List[str] | str]) -> List[str]:
        if not images:
            return []
        if isinstance(images, str):
            return [img.strip() for img in images.split(",") if img.strip()]
        return [str(img) for img in images if img]

    def _extract_sku_images(self, skus: List[dict]) -> List[str]:
        images: List[str] = []
        for sku in skus:
            pic_url = sku.get("pic_url") or sku.get("sku_pic_url")
            if pic_url:
                images.append(str(pic_url))
        return images

    def _extract_detail_images(self, item: dict) -> List[str]:
        for key in ("detail_image_urls", "detail_imgs", "desc_img", "desc_imgs"):
            images = self._normalize_image_list(item.get(key))
            if images:
                return images
        description = item.get("description")
        if isinstance(description, list):
            return [str(img) for img in description if isinstance(img, str)]
        return []

    def _safe_float(self, value: object, default: float | None) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

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
