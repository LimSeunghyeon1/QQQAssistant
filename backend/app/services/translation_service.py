from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.domain import Product, ProductLocalizedInfo, ProductOption


class TranslationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _translate_text(self, text: str, target_language: str) -> str:
        if not text:
            return ""
        return f"{text} ({target_language})"

    def _translate_list(self, texts: List[str], target_language: str) -> List[str]:
        return [self._translate_text(text, target_language) for text in texts]

    def translate_product(
        self, product_id: int, target_locale: str = "ko-KR", provider: str = "gcloud"
    ) -> ProductLocalizedInfo:
        _ = provider
        product: Product | None = self.session.get(Product, product_id)
        if not product:
            raise LookupError("Product not found")

        options: List[ProductOption] = (
            self.session.query(ProductOption)
            .filter(ProductOption.product_id == product_id)
            .all()
        )

        target_language = target_locale.split("-")[0]
        translated_title = self._translate_text(product.raw_title, target_language)

        raw_option_names = [opt.raw_name for opt in options]
        translated_option_names = self._translate_list(raw_option_names, target_language)

        for opt, translated in zip(options, translated_option_names):
            opt.localized_name = translated
            self.session.add(opt)

        localized = (
            self.session.query(ProductLocalizedInfo)
            .filter(
                ProductLocalizedInfo.product_id == product_id,
                ProductLocalizedInfo.locale == target_locale,
            )
            .first()
        )
        if not localized:
            localized = ProductLocalizedInfo(product_id=product_id, locale=target_locale)

        localized.title = translated_title
        localized.description = localized.description or ""
        localized.option_display_name_format = localized.option_display_name_format or "{option}"

        self.session.add(localized)
        self.session.flush()
        return localized
