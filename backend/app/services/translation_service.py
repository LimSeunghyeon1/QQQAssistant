from __future__ import annotations

import os
from typing import List

from google.cloud import translate_v2 as translate
from google.auth.exceptions import DefaultCredentialsError

from sqlalchemy.orm import Session

from app.config import settings
from app.models.domain import Product, ProductLocalizedInfo, ProductOption


class TranslationError(RuntimeError):
    """Raised when translation cannot be performed."""


class TranslationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.provider = settings.translation_provider.lower()
        self.translation_api_key = settings.translation_api_key
        self.google_credentials = settings.google_application_credentials
        self._client: translate.Client | None = None

    def _get_gcloud_client(self) -> translate.Client:
        if not self._client:
            client_kwargs: dict[str, str] = {}
            if self.google_credentials:
                os.environ.setdefault(
                    "GOOGLE_APPLICATION_CREDENTIALS", self.google_credentials
                )
            if self.translation_api_key:
                client_kwargs["api_key"] = self.translation_api_key

            # In test/dev environments where credentials are not provided, allow
            # the caller to surface translation failures deterministically
            # instead of raising DefaultCredentialsError here.
            try:
                self._client = translate.Client(**client_kwargs)
            except DefaultCredentialsError:
                self._client = None
        return self._client

    def _translate_text(
        self, text: str, target_language: str, provider: str | None = None
    ) -> str:
        if not text:
            return ""
        provider = (provider or self.provider).lower()
        if provider != "gcloud":
            raise ValueError(f"Unsupported translation provider: {provider}")

        client = self._get_gcloud_client()
        if client is None:
            raise TranslationError("Translation client not available")

        try:
            response = client.translate(text, target_language=target_language)
            return response["translatedText"]
        except Exception as exc:  # pragma: no cover - passthrough for clarity
            raise TranslationError("Translation request failed") from exc

    def _translate_list(
        self, texts: List[str], target_language: str, provider: str | None = None
    ) -> List[str]:
        return [
            self._translate_text(text, target_language, provider=provider)
            for text in texts
        ]

    def translate_product(
        self, product_id: int, target_locale: str = "ko-KR", provider: str = "gcloud"
    ) -> ProductLocalizedInfo:
        provider_to_use = provider or self.provider
        product: Product | None = self.session.get(Product, product_id)
        if not product:
            raise LookupError("Product not found")

        options: List[ProductOption] = (
            self.session.query(ProductOption)
            .filter(ProductOption.product_id == product_id)
            .all()
        )

        target_language = target_locale.split("-")[0]
        translated_title = self._translate_text(
            product.raw_title, target_language, provider=provider_to_use
        )
        translated_description = self._translate_text(
            product.raw_description or "",
            target_language,
            provider=provider_to_use,
        )

        raw_option_names = [opt.raw_name for opt in options]
        translated_option_names = self._translate_list(
            raw_option_names, target_language, provider=provider_to_use
        )

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
        localized.description = translated_description or localized.description or ""
        localized.option_display_name_format = localized.option_display_name_format or "{option}"

        self.session.add(localized)
        self.session.flush()
        return localized
