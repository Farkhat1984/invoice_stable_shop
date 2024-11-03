# controllers/base_api_controller.py
from typing import Callable, Optional, Dict, Any
from kivy.network.urlrequest import UrlRequest
from functools import partial
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



class BaseAPIController:
    def __init__(self, base_url: str = "http://localhost:8000", auth_controller: Optional[Any] = None):
        self.base_url = base_url
        self.auth_controller = auth_controller

    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Generate headers for the HTTP request."""
        headers = {
            "Content-Type": content_type,
            "Accept": "application/json"
        }
        if self.auth_controller and getattr(self.auth_controller, 'token', None):
            headers["Authorization"] = f"Bearer {self.auth_controller.token}"
        logger.debug(f"Generated headers: {headers}")
        return headers

    def _handle_error(self, req: UrlRequest, error: Exception, error_callback: Optional[Callable[[str], None]]):
        """Handle errors from HTTP requests."""
        logger.error(f"Request error: {error}")
        error_message = str(error)

        if req.result:
            try:
                if isinstance(req.result, dict):
                    error_data = req.result
                    error_message = error_data.get('detail', error_message)
                elif isinstance(req.result, (str, bytes, bytearray)):
                    error_data = json.loads(req.result)
                    error_message = error_data.get('detail', error_message)
                else:
                    logger.warning(f"Unexpected result type: {type(req.result)}")
            except json.JSONDecodeError:
                logger.warning("Failed to decode error response as JSON")
            except Exception as e:
                logger.exception("Error while processing request result")
                error_message = f"Error processing response: {str(e)}"

        if error_callback:
            error_callback(error_message)

    def _make_request(
            self,
            endpoint: str,
            method: str = 'GET',
            req_body: Optional[str] = None,
            headers: Optional[Dict[str, str]] = None,
            success_callback: Optional[Callable[[UrlRequest, Any], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None
    ):
        """General method to make HTTP requests."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Making {method} request to {url}")
        logger.debug(f"Request body: {req_body}")
        logger.debug(f"Request headers: {headers or self._get_headers()}")

        UrlRequest(
            url,
            req_body=req_body,
            method=method,
            req_headers=headers or self._get_headers(),
            on_success=lambda req, result: success_callback(req, result) if success_callback else None,
            on_error=partial(self._handle_error, error_callback=error_callback),
            on_failure=partial(self._handle_error, error_callback=error_callback)
        )
