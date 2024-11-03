from typing import Dict, Any, Optional, Callable
from functools import partial
from .base_api_controller import BaseAPIController
import logging
from urllib.parse import urlencode, quote
from datetime import datetime

logger = logging.getLogger(__name__)


class HistoryAPIController(BaseAPIController):
    def __init__(self, base_url: str = "http://localhost:8000", auth_controller: Optional[Any] = None):
        super().__init__(base_url=base_url, auth_controller=auth_controller)

    def _prepare_filters(self, filters: Optional[Dict[str, Any]] = None) -> str:
        """
        Prepare filters for URL with proper encoding.
        """
        if filters is None:
            filters = {}

        # Get default shop_id from auth_controller if available
        if self.auth_controller and hasattr(self.auth_controller, 'current_shop_id'):
            if 'shop_id' not in filters and self.auth_controller.current_shop_id:
                filters['shop_id'] = self.auth_controller.current_shop_id

        encoded_filters = {}
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, datetime):
                    encoded_filters[key] = value.isoformat()
                elif isinstance(value, bool):
                    encoded_filters[key] = str(value).lower()
                elif isinstance(value, (int, float)):
                    encoded_filters[key] = str(value)
                else:
                    encoded_filters[key] = str(value)

        # Add default pagination parameters if not provided
        if 'skip' not in encoded_filters:
            encoded_filters['skip'] = '0'
        if 'limit' not in encoded_filters:
            encoded_filters['limit'] = '100'

        if encoded_filters:
            return "?" + urlencode(encoded_filters, quote_via=quote)
        return ""

    def get_invoices(
            self,
            success_callback: Optional[Callable[[Any], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None,
            filters: Optional[Dict[str, Any]] = None
    ):
        """Retrieve list of invoices with optional filters."""
        endpoint = "/api/v1/invoices/"

        # Add filters to URL
        query_string = self._prepare_filters(filters)
        if query_string:
            endpoint += query_string
            logger.debug(f"Fetching invoices with filters: {filters}")
            logger.debug(f"Constructed endpoint: {endpoint}")

        def success_wrapper(req, result):
            """Handle successful response with format validation"""
            try:
                if success_callback:
                    if isinstance(result, (list, dict)):
                        success_callback(result)
                    else:
                        logger.error(f"Unexpected response format: {result}")
                        if error_callback:
                            error_callback("Unexpected response format from server")
            except Exception as e:
                logger.error(f"Error in success callback: {e}")
                if error_callback:
                    error_callback(str(e))

        self._make_request(
            endpoint=endpoint,
            method='GET',
            headers=self._get_headers(),
            success_callback=success_wrapper,
            error_callback=error_callback
        )

    def get_invoice_stats(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            shop_id: Optional[int] = None,
            success_callback: Optional[Callable[[Any], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None
    ):
        """Get invoice statistics."""
        endpoint = "/api/v1/invoices/stats/summary"

        filters = {}
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if shop_id:
            filters['shop_id'] = shop_id
        elif self.auth_controller and hasattr(self.auth_controller, 'current_shop_id'):
            filters['shop_id'] = self.auth_controller.current_shop_id

        query_string = self._prepare_filters(filters)
        if query_string:
            endpoint += query_string

        logger.debug(f"Fetching invoice stats with filters: {filters}")

        def success_wrapper(req, result):
            """Handle successful response with format validation"""
            try:
                if success_callback:
                    if isinstance(result, dict):
                        success_callback(result)
                    else:
                        logger.error(f"Unexpected response format: {result}")
                        if error_callback:
                            error_callback("Unexpected response format from server")
            except Exception as e:
                logger.error(f"Error in success callback: {e}")
                if error_callback:
                    error_callback(str(e))

        self._make_request(
            endpoint=endpoint,
            method='GET',
            headers=self._get_headers(),
            success_callback=success_wrapper,
            error_callback=error_callback
        )

    def get_last_invoice(
            self,
            success_callback: Optional[Callable[[Any], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None
    ):
        """Retrieve the last created invoice."""
        endpoint = "/api/v1/invoices/last"
        logger.debug("Fetching last invoice")

        def success_wrapper(req, result):
            """Handle successful response with format validation"""
            try:
                if success_callback:
                    if isinstance(result, dict):
                        # Update last_invoice_id in auth_controller if available
                        if self.auth_controller and hasattr(self.auth_controller, 'last_invoice_id'):
                            self.auth_controller.last_invoice_id = result.get('id')
                        success_callback(result)
                    else:
                        logger.error(f"Unexpected response format: {result}")
                        if error_callback:
                            error_callback("Unexpected response format from server")
            except Exception as e:
                logger.error(f"Error in success callback: {e}")
                if error_callback:
                    error_callback(str(e))

        self._make_request(
            endpoint=endpoint,
            method='GET',
            headers=self._get_headers(),
            success_callback=success_wrapper,
            error_callback=error_callback
        )

    def delete_invoice(
            self,
            invoice_id: int,
            success_callback: Optional[Callable[[], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None
    ):
        """Delete a specific invoice."""
        if not isinstance(invoice_id, int):
            if error_callback:
                error_callback("Invalid invoice ID")
            return

        endpoint = f"/api/v1/invoices/{invoice_id}"
        logger.debug(f"Attempting to delete invoice with ID: {invoice_id}")

        def success_wrapper(req, result):
            """Handle successful deletion and update last_invoice_id if needed"""
            if self.auth_controller and hasattr(self.auth_controller, 'last_invoice_id'):
                if self.auth_controller.last_invoice_id == invoice_id:
                    self.auth_controller.last_invoice_id = None
            if success_callback:
                success_callback()

        self._make_request(
            endpoint=endpoint,
            method='DELETE',
            headers=self._get_headers(),
            success_callback=success_wrapper,
            error_callback=error_callback
        )

    def get_invoice_details(
            self,
            invoice_id: int,
            success_callback: Optional[Callable[[Any], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None
    ):
        """Retrieve detailed information about a specific invoice."""
        if not isinstance(invoice_id, int):
            if error_callback:
                error_callback("Invalid invoice ID")
            return

        endpoint = f"/api/v1/invoices/{invoice_id}"
        logger.debug(f"Fetching details for invoice ID: {invoice_id}")

        def success_wrapper(req, result):
            """Handle successful response with format validation"""
            try:
                if success_callback:
                    if isinstance(result, dict):
                        success_callback(result)
                    else:
                        logger.error(f"Unexpected response format: {result}")
                        if error_callback:
                            error_callback("Unexpected response format from server")
            except Exception as e:
                logger.error(f"Error in success callback: {e}")
                if error_callback:
                    error_callback(str(e))

        self._make_request(
            endpoint=endpoint,
            method='GET',
            headers=self._get_headers(),
            success_callback=success_wrapper,
            error_callback=error_callback
        )