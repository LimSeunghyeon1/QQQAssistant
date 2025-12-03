from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
from urllib.parse import urlparse

import requests
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)


BoundingBox = Tuple[int, int, int, int]


@dataclass
class ImageCleanupResult:
    source_url: str
    cleaned_url: str | None
    success: bool
    error: str | None = None


class ImageCleanupService:
    """Lightweight OCR-style text masking for product images.

    The service avoids heavyweight OCR dependencies by using a simple
    high-contrast detector to approximate text regions. Regions are blurred
    and saved to a local storage directory. Errors are logged and bubbled up
    as ``success=False`` while preserving the original URL for callers.
    """

    def __init__(self, storage_dir: str | os.PathLike = "storage/cleaned") -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def cleanup_images(self, image_urls: Sequence[str]) -> List[str]:
        """Download, mask, and store each image.

        Returns a list aligned with ``image_urls`` where failed items fall back
        to the original URL.
        """

        results: List[str] = []
        for url in image_urls:
            result = await asyncio.to_thread(self._cleanup_single_image, url)
            if not result.success:
                logger.warning(
                    "Image cleanup failed; preserving original", extra={"url": url, "error": result.error}
                )
            results.append(result.cleaned_url or url)
        return results

    def _cleanup_single_image(self, image_url: str) -> ImageCleanupResult:
        try:
            content = self._download_image(image_url)
            image = Image.open(BytesIO(content)).convert("RGB")

            boxes = self._detect_text_regions(image)
            if boxes:
                image = self._mask_regions(image, boxes)

            stored_path = self._upload_image(image)
            return ImageCleanupResult(
                source_url=image_url, cleaned_url=str(stored_path), success=True
            )
        except Exception as exc:  # noqa: BLE001
            return ImageCleanupResult(
                source_url=image_url, cleaned_url=None, success=False, error=str(exc)
            )

    def _download_image(self, image_url: str) -> bytes:
        parsed = urlparse(image_url)
        if parsed.scheme in {"", "file"}:
            path = Path(parsed.path)
            return path.read_bytes()

        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        return response.content

    def _detect_text_regions(self, image: Image.Image) -> List[BoundingBox]:
        """Detect high-contrast regions as a proxy for text areas.

        A simple luminance threshold highlights non-background pixels and
        returns a single bounding box that wraps them. This works well for
        watermark-like overlays in fixtures without external OCR engines.
        """

        grayscale = image.convert("L")
        pixels = grayscale.load()
        width, height = grayscale.size
        threshold = 240

        xs: List[int] = []
        ys: List[int] = []

        for y in range(height):
            for x in range(width):
                if pixels[x, y] < threshold:
                    xs.append(x)
                    ys.append(y)

        if not xs or not ys:
            return []

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        padding = 4
        min_x = max(min_x - padding, 0)
        min_y = max(min_y - padding, 0)
        max_x = min(max_x + padding, width - 1)
        max_y = min(max_y + padding, height - 1)

        return [(min_x, min_y, max_x, max_y)]

    def _mask_regions(self, image: Image.Image, boxes: Iterable[BoundingBox]) -> Image.Image:
        masked = image.copy()
        for box in boxes:
            x1, y1, x2, y2 = box
            region = masked.crop((x1, y1, x2, y2))
            blurred = region.filter(ImageFilter.GaussianBlur(radius=6))
            masked.paste(blurred, (x1, y1, x2, y2))
        return masked

    def _upload_image(self, image: Image.Image) -> Path:
        filename = f"cleaned_{int(time.time() * 1_000_000)}.png"
        target = self.storage_dir / filename
        image.save(target, format="PNG")
        return target
