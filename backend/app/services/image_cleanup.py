from __future__ import annotations

from typing import Iterable, List


class ImageCleanupService:
    """Lightweight image cleanup stub that can later host OCR-based removal.

    For now we simply normalize URLs and de-duplicate them while keeping a
    deterministic contract so downstream code can rely on the pipeline output.
    """

    def clean_images(self, image_urls: Iterable[str]) -> List[str]:
        cleaned: list[str] = []
        for url in image_urls:
            normalized = url.strip()
            if not normalized:
                continue
            cleaned_url = self._mark_clean(normalized)
            if cleaned_url not in cleaned:
                cleaned.append(cleaned_url)
        return cleaned

    def _mark_clean(self, url: str) -> str:
        # Without a heavy OCR dependency we just append a marker query string
        # to indicate that the URL passed through the cleanup step.
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}cleaned=1"
