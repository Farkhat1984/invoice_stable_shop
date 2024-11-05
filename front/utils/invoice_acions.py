
import os
import subprocess
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from front.utils.pdf_generator import InvoicePDFGenerator
from front.utils.share_pdf import ShareManager





class InvoiceActionsMixin:
    def show_message(self, message: str) -> None:
        """Utility method to show a popup message."""
        popup = Popup(
            title='Сообщение',
            content=Label(text=message),
            size_hint=(None, None),
            size=(400, 200)
        )
        popup.open()

    def print_invoice(self):
        """Handles the printing of the invoice as a PDF."""
        try:
            # Ensure there is data to print
            invoice_data = self._collect_invoice_data()
            if not invoice_data["items"]:
                self.show_message("Ошибка: накладная пуста")
                return

            # Create directory for PDFs if it doesn't exist
            pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated_pdfs')
            os.makedirs(pdf_dir, exist_ok=True)

            # Generate filename
            invoice_id = self.displayed_text or 'new'
            filename = InvoicePDFGenerator.get_invoice_filename(invoice_id)
            pdf_path = os.path.join(pdf_dir, filename)

            # Generate PDF
            pdf_generator = InvoicePDFGenerator()
            generated_pdf = pdf_generator.generate_pdf(invoice_data, pdf_path)

            # Open PDF with the system viewer
            if os.path.exists(generated_pdf):
                if os.name == 'nt':  # Windows
                    os.startfile(generated_pdf)
                elif os.name == 'posix':  # macOS and Linux
                    subprocess.call(['xdg-open', generated_pdf])  # Linux
                    # subprocess.call(['open', generated_pdf])  # macOS

                self.show_message("PDF накладной создан и открыт")
            else:
                self.show_message("Ошибка при создании PDF")

        except Exception as e:
            print(f"Error generating PDF: {e}")
            self.show_message(f"Ошибка при создании PDF: {str(e)}")

    def share_invoice(self):
        """Handles sharing the invoice via available sharing options."""
        try:
            # Check for data
            invoice_data = self._collect_invoice_data()
            if not invoice_data["items"]:
                self.show_message("Ошибка: накладная пуста")
                return

            # Create PDF
            pdf_generator = InvoicePDFGenerator()
            invoice_id = self.displayed_text or 'new'
            filename = InvoicePDFGenerator.get_invoice_filename(invoice_id)
            pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated_pdfs', filename)
            generated_pdf = pdf_generator.generate_pdf(invoice_data, pdf_path)

            if not os.path.exists(generated_pdf):
                self.show_message("Ошибка при создании PDF для отправки")
                return

            # Show sharing options
            share_manager = ShareManager()
            share_manager.show_share_popup(generated_pdf)

        except Exception as e:
            print(f"Error sharing invoice: {e}")
            self.show_message(f"Ошибка при отправке накладной: {str(e)}")
