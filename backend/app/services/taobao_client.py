from __future__ import annotations

import os
from typing import Any, Dict, Optional

import iop


class TaobaoClient:
    """Minimal Taobao IOP API client.

    Uses environment variables when explicit credentials are not provided:
    - ``TAOBAO_APP_KEY``
    - ``TAOBAO_APP_SECRET``
    - ``TAOBAO_SESSION_KEY`` (optional access token)
    - ``TAOBAO_CALLBACK_URL`` (required callback URL for the IOP gateway)

    The client assumes a valid seller access token already exists and does not
    implement the OAuth flow for obtaining one.
    """

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> None:
        self.app_key = app_key or os.getenv("TAOBAO_APP_KEY", "")
        self.app_secret = app_secret or os.getenv("TAOBAO_APP_SECRET", "")
        self.access_token = access_token or os.getenv("TAOBAO_SESSION_KEY", "")
        self.callback_url = callback_url or os.getenv("TAOBAO_CALLBACK_URL", "")

        if not self.app_key or not self.app_secret:
            raise ValueError("TAOBAO_APP_KEY / TAOBAO_APP_SECRET must be set")

        if not self.callback_url:
            raise ValueError("TAOBAO_CALLBACK_URL must be set")

        self.client = iop.IopClient(self.callback_url, self.app_key, self.app_secret)

        if not self.access_token:
            # The access token can be overridden per call if not set globally.
            print("[TaobaoClient] WARNING: access_token is empty.")

    def execute(
        self,
        api_params: Optional[Dict[str, Any]] = None,
        *,
        access_token: Optional[str] = None,
        http_method: str = "GET",
    ) -> Any:
        """Execute a Taobao IOP call for ``/product/get``.

        Args:
            api_params: Business parameters for the ``/product/get`` API.
            access_token: Optional override for the access token.
            http_method: HTTP verb for the request (GET by default).
        """

        request = iop.IopRequest("/product/get", http_method.upper())
        for key, value in (api_params or {}).items():
            request.add_api_param(key, value)

        token = access_token or self.access_token
        return self.client.execute(request, token)

    def get_item_detail(
        self,
        num_iid: int | str,
        *,
        access_token: Optional[str] = None,
        item_source_market: Optional[str] = None,
    ) -> Any:
        """Convenience wrapper for ``/product/get`` using a product identifier."""

        params = {"num_iid": num_iid}
        if item_source_market:
            params["item_source_market"] = item_source_market
        return self.execute(api_params=params, access_token=access_token)
