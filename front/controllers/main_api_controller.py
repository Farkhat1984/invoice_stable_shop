from typing import Optional, Any, Callable
from controllers.base_api_controller import BaseAPIController, logger


class MainViewApiController(BaseAPIController):
    def __init__(self, base_url: str = "http://localhost:8000", auth_controller: Optional[Any] = None):
        super().__init__(base_url=base_url, auth_controller=auth_controller)

    def get_next_invoice_number(
            self,
            success_callback: Optional[Callable[[str], None]] = None,
            error_callback: Optional[Callable[[str], None]] = None
    ):
        """Get the next invoice number by fetching the last invoice and incrementing its ID."""
        endpoint = "/api/v1/invoices/last"
        logger.debug("Fetching last invoice number")

        def handle_success(req, result):
            """Handle successful last invoice fetch and calculate next number."""
            try:
                if isinstance(result, dict) and 'id' in result:
                    last_id = int(result['id'])
                    next_number = str(last_id + 1) # Pad with zeros to maintain consistent format

                    if success_callback:
                        success_callback(next_number)

                    # Optionally update auth controller if needed
                    if self.auth_controller and hasattr(self.auth_controller, 'last_invoice_id'):
                        self.auth_controller.last_invoice_id = last_id
                else:
                    raise ValueError("Invalid response format: 'id' field not found")

            except (ValueError, TypeError) as e:
                logger.error(f"Error processing invoice number: {e}")
                if error_callback:
                    error_callback(f"Error processing invoice number: {e}")

        def handle_error(error_msg):
            """Handle case where no last invoice exists."""
            logger.warning(f"Error fetching last invoice: {error_msg}")
            # If no last invoice exists, start from 1
            if "404" in str(error_msg) or "No last invoice found" in str(error_msg):
                if success_callback:
                    success_callback("0001")
            elif error_callback:
                error_callback(str(error_msg))

        self._make_request(
            endpoint=endpoint,
            method='GET',
            headers=self._get_headers(),
            success_callback=handle_success,
            error_callback=handle_error
        )