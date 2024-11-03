import json
from functools import partial
from typing import Optional, Callable, Any
from kivy.network.urlrequest import UrlRequest
from .base_api_controller import BaseAPIController
import logging
import base64

logger = logging.getLogger(__name__)


class AuthAPIController(BaseAPIController):
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url=base_url)
        self.token: Optional[str] = None
        self.current_shop_id: Optional[int] = None
        self.last_invoice_id: Optional[int] = None
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def _extract_token_payload(self, token: str) -> dict:
        """Extract payload from JWT token without verification"""
        try:
            # Split the token and get the payload part
            parts = token.split('.')
            if len(parts) != 3:
                return {}

            # Decode the payload
            padding = '=' * (4 - len(parts[1]) % 4)
            payload = base64.urlsafe_b64decode(parts[1] + padding)
            return json.loads(payload)
        except Exception as e:
            logger.warning(f"Failed to extract token payload: {e}")
            return {}

    def _handle_token_response(self, req: UrlRequest, result: Any, success_callback: Optional[Callable[[Any], None]]):
        """Handle successful token response (login/register)."""
        self.token = result.get('access_token')

        if self.token:
            # Extract payload directly from token
            payload = self._extract_token_payload(self.token)
            self.current_shop_id = payload.get("user_shop_id")
            self.last_invoice_id = payload.get("last_invoice_id")

            logger.info(
                f"Token received and processed. Shop ID: {self.current_shop_id}, Last Invoice ID: {self.last_invoice_id}")
        else:
            logger.warning("No token received in response")

        logger.info("Authentication successful. Token obtained.")
        if success_callback:
            success_callback(result)

    def get_shop_id(self) -> Optional[int]:
        """Get current shop ID"""
        if self.current_shop_id is None and self.token:
            # Try to extract from token if not set
            payload = self._extract_token_payload(self.token)
            self.current_shop_id = payload.get("user_shop_id")
        return self.current_shop_id

    def login(
            self,
            username: str,
            password: str,
            success_callback: Optional[Callable[[Any], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Asynchronous login via API.
        """
        login_url = "/api/v1/auth/token"
        form_data = f"username={username}&password={password}"
        logger.debug(f"Attempting to login user: {username}")

        self._make_request(
            endpoint=login_url,
            method='POST',
            req_body=form_data,
            headers=self.headers,
            success_callback=partial(self._handle_token_response, success_callback=success_callback),
            error_callback=error_callback
        )