# controllers/invoice_api_controller.py
from datetime import timedelta, datetime
from typing import Dict, Any, Optional, Callable
from .base_api_controller import BaseAPIController
import json
import logging

logger = logging.getLogger(__name__)


class InvoiceAPIController(BaseAPIController):
    def __init__(self, base_url: str = "http://localhost:8000", auth_controller: Optional[Any] = None):
        super().__init__(base_url=base_url, auth_controller=auth_controller)

    def create_invoice(
            self,
            invoice_data: Dict[str, Any],
            success_callback: Optional[Callable[[Any], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None
    ):
        """Create a new invoice."""
        endpoint = "/api/v1/invoices/"
        logger.debug(f"Creating invoice with data: {invoice_data}")

        # Get shop_id from auth_controller or invoice_data
        default_shop_id = getattr(self.auth_controller, 'current_shop_id', None)
        if not default_shop_id:
            logger.warning("No current_shop_id found in auth_controller")

        # Prepare invoice data for API
        try:
            api_invoice_data = {
                "shop_id": int(invoice_data.get("shop_id", default_shop_id or 0)),
                # Use 0 to trigger API-side validation
                "contact_info": str(invoice_data.get("contact", "")),
                "additional_info": str(invoice_data.get("additional_info", "")),
                "total_amount": float(invoice_data.get("total", 0)),
                "is_paid": bool(invoice_data.get("is_paid", False)),
                "items": [
                    {
                        "name": item["name"],
                        "article": item.get("article", ""),
                        "quantity": float(item["quantity"]),
                        "price": float(item["price"]),
                        "total": float(item["sum"])
                    }
                    for item in invoice_data.get("items", [])
                    if item.get("name") and item.get("quantity") and item.get("price")
                ]
            }

            # Remove shop_id if it's 0 to let the API use the current user's default shop
            if api_invoice_data["shop_id"] == 0:
                del api_invoice_data["shop_id"]

        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Invalid invoice data: {e}")
            if error_callback:
                error_callback(f"Invalid invoice data: {e}")
            return

        logger.debug(f"Prepared invoice data for API: {api_invoice_data}")

        def handle_create_success(req, result):
            """Handle successful invoice creation and update auth controller if needed."""
            # Update last_invoice_id in auth_controller if available
            if self.auth_controller and hasattr(self.auth_controller, 'last_invoice_id'):
                if 'id' in result:
                    self.auth_controller.last_invoice_id = result['id']
                # If new token is provided in response, update it
                if 'new_token' in result:
                    self.auth_controller.token = result['new_token']

            if success_callback:
                success_callback(result)

        req_body = json.dumps(api_invoice_data)
        self._make_request(
            endpoint=endpoint,
            method='POST',
            req_body=req_body,
            headers=self._get_headers(),
            success_callback=handle_create_success,
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
        params = []

        if start_date:
            params.append(f"start_date={start_date.isoformat()}")
        if end_date:
            params.append(f"end_date={end_date.isoformat()}")
        if shop_id:
            params.append(f"shop_id={shop_id}")

        if params:
            endpoint = f"{endpoint}?{'&'.join(params)}"

        logger.debug(f"Fetching invoice stats with params: {params}")

        self._make_request(
            endpoint=endpoint,
            method='GET',
            headers=self._get_headers(),
            success_callback=lambda req, result: success_callback(result) if success_callback else None,
            error_callback=error_callback
        )

    def update_invoice(
            self,
            invoice_id: int,
            invoice_data: Dict[str, Any],
            success_callback: Optional[Callable[[Any], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None
    ):
        """Update an existing invoice."""
        endpoint = f"/api/v1/invoices/{invoice_id}"
        logger.debug(f"Updating invoice ID: {invoice_id} with data: {invoice_data}")

        # Prepare update data
        try:
            update_data = {
                "contact_info": str(invoice_data.get("contact", "")),
                "additional_info": str(invoice_data.get("additional_info", "")),
                "total_amount": float(invoice_data.get("total", 0)),
                "is_paid": bool(invoice_data.get("is_paid", False)),
                "items": [
                    {
                        "name": item["name"],
                        "article": item.get("article", ""),
                        "quantity": float(item["quantity"]),
                        "price": float(item["price"]),
                        "total": float(item["sum"])
                    }
                    for item in invoice_data.get("items", [])
                    if item.get("name") and item.get("quantity") and item.get("price")
                ]
            }
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Invalid invoice update data: {e}")
            if error_callback:
                error_callback(f"Invalid invoice update data: {e}")
            return

        logger.debug(f"Prepared update data for API: {update_data}")

        req_body = json.dumps(update_data)
        self._make_request(
            endpoint=endpoint,
            method='PATCH',
            req_body=req_body,
            headers=self._get_headers(),
            success_callback=lambda req, result: success_callback(result) if success_callback else None,
            error_callback=error_callback
        )

    def get_invoice_details(
            self,
            invoice_id: int,
            success_callback: Optional[Callable[[Any], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None
    ):
        """Retrieve detailed information about a specific invoice."""
        endpoint = f"/api/v1/invoices/{invoice_id}"
        logger.debug(f"Fetching invoice details for ID: {invoice_id}")

        self._make_request(
            endpoint=endpoint,
            method='GET',
            headers=self._get_headers(),
            success_callback=lambda req, result: success_callback(result) if success_callback else None,
            error_callback=error_callback
        )

    def update_invoice_status(
            self,
            invoice_id: int,
            is_paid: bool,
            success_callback: Optional[Callable[[Any], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None
    ):
        """Update the payment status of an invoice."""
        endpoint = f"/api/v1/invoices/{invoice_id}/status"
        logger.debug(f"Updating invoice ID: {invoice_id} payment status to: {is_paid}")

        data = {"is_paid": is_paid}
        req_body = json.dumps(data)

        self._make_request(
            endpoint=endpoint,
            method='PATCH',
            req_body=req_body,
            headers=self._get_headers(),
            success_callback=lambda req, result: success_callback(result) if success_callback else None,
            error_callback=error_callback
        )

    def delete_invoice(
            self,
            invoice_id: int,
            success_callback: Optional[Callable[[], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None
    ):
        """Delete a specific invoice."""
        endpoint = f"/api/v1/invoices/{invoice_id}"
        logger.debug(f"Attempting to delete invoice ID: {invoice_id}")

        self._make_request(
            endpoint=endpoint,
            method='DELETE',
            headers=self._get_headers(),
            success_callback=lambda req, result: success_callback() if success_callback else None,
            error_callback=error_callback
        )