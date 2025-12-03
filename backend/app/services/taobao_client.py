from __future__ import annotations

import hashlib
import os
import time
from typing import Any, Dict, Optional

import requests


class TaobaoClient:
    """Minimal Taobao TOP API client.

    Uses environment variables when explicit credentials are not provided:
    - ``TAOBAO_APP_KEY``
    - ``TAOBAO_APP_SECRET``
    - ``TAOBAO_SESSION_KEY``
    - ``TAOBAO_API_URL`` (optional, defaults to the official router URL)

    The client assumes a valid seller ``session`` token already exists and does
    not implement the OAuth flow for obtaining one.
    """

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        session_key: Optional[str] = None,
        api_url: Optional[str] = None,
    ) -> None:
        self.app_key = app_key or os.getenv("TAOBAO_APP_KEY", "")
        self.app_secret = app_secret or os.getenv("TAOBAO_APP_SECRET", "")
        self.session_key = session_key or os.getenv("TAOBAO_SESSION_KEY", "")

        # Official gateway URL
        self.api_url = api_url or os.getenv(
            "TAOBAO_API_URL", "https://gw.api.taobao.com/router/rest"
        )

        if not self.app_key or not self.app_secret:
            print(
                "[TaobaoClient] WARNING: TAOBAO_APP_KEY / TAOBAO_APP_SECRET are empty; "
                "real API calls will fail without credentials."
            )

        if not self.session_key:
            # Many product/order APIs require a session token.
            # It can be overridden per call if not needed.
            print("[TaobaoClient] WARNING: session_key is empty.")

    def _sign(self, params: Dict[str, Any]) -> str:
        """Create TOP API signature using the default MD5 algorithm.

        Algorithm::

            sign = UPPERCASE( MD5(app_secret + concat(sorted(params)) + app_secret) )

        - Keys are sorted alphabetically.
        - The ``sign`` parameter itself is excluded from the base string.
        """

        sorted_items = sorted(
            (k, v) for k, v in params.items() if k != "sign" and v is not None
        )
        base_str = self.app_secret + "".join(f"{k}{v}" for k, v in sorted_items) + self.app_secret

        md5 = hashlib.md5()
        md5.update(base_str.encode("utf-8"))
        return md5.hexdigest().upper()

    def _build_common_params(
        self,
        method: str,
        session: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Merge TOP common params with business params."""

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        params: Dict[str, Any] = {
            "method": method,
            "app_key": self.app_key,
            "timestamp": timestamp,
            "format": "json",
            "v": "2.0",
            "sign_method": "md5",
        }

        if session or self.session_key:
            params["session"] = session or self.session_key

        if extra:
            params.update(extra)

        params["sign"] = self._sign(params)
        return params

    def execute(
        self,
        method: str,
        biz_params: Optional[Dict[str, Any]] = None,
        *,
        session: Optional[str] = None,
        http_method: str = "POST",
        timeout: int = 10,
    ) -> Dict[str, Any]:
        """Execute a Taobao TOP API call.

        Args:
            method: API method name (e.g., ``"taobao.item.get"``).
            biz_params: Business parameters for the API.
            session: Optional override for the session key.
            http_method: HTTP verb for the request (POST by default).
            timeout: Timeout in seconds for the request.
        """

        common = self._build_common_params(method, session=session, extra=biz_params)

        if http_method.upper() == "GET":
            resp = requests.get(self.api_url, params=common, timeout=timeout)
        else:
            resp = requests.post(self.api_url, data=common, timeout=timeout)

        resp.raise_for_status()
        return resp.json()

    def get_item_detail(self, num_iid: int | str) -> Dict[str, Any]:
        """Example wrapper for ``taobao.item.get`` (or similar) API."""

        method = "taobao.item.get"  # Replace with the exact method you need.
        biz_params = {
            "num_iid": num_iid,
            "fields": "num_iid,title,price,pic_url,sku,volume",
        }
        return self.execute(method, biz_params=biz_params)

    def get_trades_sold(
        self,
        start_created: str,
        end_created: str,
        page_no: int = 1,
        page_size: int = 40,
    ) -> Dict[str, Any]:
        """Example wrapper for ``taobao.trades.sold.get`` API."""

        method = "taobao.trades.sold.get"
        biz_params = {
            "start_created": start_created,
            "end_created": end_created,
            "page_no": page_no,
            "page_size": page_size,
            "fields": "tid,buyer_nick,created,modified,status,total_fee",
        }
        return self.execute(method, biz_params=biz_params)
