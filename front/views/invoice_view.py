# views/invoice_view.py
from tkinter import Label

from kivy.clock import Clock
from datetime import datetime, timedelta
from typing import Dict, Any
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from front.views.invoice_table import InvoiceTable
from front.controllers.invoice_api_controller import InvoiceAPIController, logger
from front.utils.invoice_acions import InvoiceActionsMixin


class InvoiceView(Screen, InvoiceActionsMixin):
    auth_controller = ObjectProperty(None)
    displayed_text = StringProperty("Здесь появится текст")

    def __init__(self, screen_manager, **kwargs):
        super().__init__(name='invoice', **kwargs)

        self.sm = screen_manager
        self.sm.add_widget(self)
        self.editing_invoice = None
        self.payment_status_value = 0
        self.api_controller = None
        self.current_shop_id = None
        Clock.schedule_once(self._initialize_view)
        self.contact_input = self.ids.contact
        self.additional_info_input = self.ids.additional_info
        self.date_label = self.ids.date
        self.payment_button = self.ids.payment_button
        self.table_content = self.ids.table_content
        self.total_sum_label = self.ids.total_sum

    def on_auth_controller(self, instance, value):
        if value and value.token:
            self.api_controller = InvoiceAPIController(
                auth_controller=value,
                base_url="http://localhost:8000"
            )
            self.current_shop_id = value.get_shop_id()
        else:
            pass

    def _initialize_view(self, dt: float) -> None:
        self.add_initial_rows()
        self.update_date_time()
        self.payment_button.text = 'Не оплачено!'

    def _collect_invoice_data(self) -> Dict[str, Any]:
        if self.current_shop_id is None and self.auth_controller:
            self.current_shop_id = self.auth_controller.get_shop_id()

        return {
            "shop_id": self.current_shop_id,
            "id": self.displayed_text,
            "contact": self.contact_input.text,
            "additional_info": self.additional_info_input.text,
            "total": self.calculate_total(),
            "is_paid": self.payment_status_value == 1,
            "created_at": self.date_label.text,
            "items": [
                {
                    "name": row.name_input.text,
                    "quantity": float(row.quantity_input.text),
                    "price": float(row.price_input.text),
                    "sum": float(row.sum_label.text)
                }
                for row in self.table_content.children
                if row.quantity_input.text and row.price_input.text
            ]
        }

    def clear_invoice_form(self) -> None:
        self.contact_input.text = ''
        self.additional_info_input.text = ''

        for row in self.table_content.children:
            row.reset_values()

        self.payment_status_value = 0
        self.payment_button.text = 'Не оплачено!'
        self.editing_invoice = None
        self.update_total()
        self.update_date_time()

    def load_invoice_data(self, invoice_data: Dict[str, Any]):
        try:
            print(f"Loading invoice data: {invoice_data}")  # Debugging

            self.editing_invoice = invoice_data.get('id')
            self.displayed_text = str(invoice_data.get('id'))
            self.contact_input.text = invoice_data.get('contact_info', '')
            self.additional_info_input.text = invoice_data.get('additional_info', '')
            self.date_label.text = invoice_data.get('created_at', '').split('T')[0]
            if 'shop_id' in invoice_data:
                self.current_shop_id = invoice_data['shop_id']

            self.payment_status_value = 1 if invoice_data.get('is_paid', False) else 0
            self.payment_button.text = 'Оплачено!' if self.payment_status_value == 1 else 'Не оплачено!'

            self.table_content.clear_widgets()

            items = invoice_data.get('items', [])
            for item in items:
                table_row = InvoiceTable()
                table_row.name_input.text = item.get('name', '')
                table_row.quantity_input.text = str(item.get('quantity', '0'))
                table_row.price_input.text = str(item.get('price', '0'))
                table_row.bind_total_update(self.update_total)
                self.table_content.add_widget(table_row)

            for _ in range(10 - len(self.table_content.children)):
                self.add_row()

            self._renumber_rows()
            self.update_total()
            print("Invoice data loaded successfully")

        except Exception as e:
            print(f"Error loading invoice data: {e}")
            self.show_message(f"Ошибка при загрузке данных накладной: {str(e)}")

    def update_invoice_status(self):
        if not self.api_controller:
            self.show_message("Ошибка: API контроллер не инициализирован")
            return

        if not self.editing_invoice:
            return

        try:
            invoice_data = self._collect_invoice_data()
            print(f"Updating invoice {self.editing_invoice} with status: {self.payment_status_value}")  # Debugging

            self.api_controller.update_invoice(
                self.editing_invoice,
                invoice_data,
                success_callback=self._on_status_update_success,
                error_callback=self._on_status_update_error
            )
        except Exception as e:
            print(f"Error in update_invoice_status: {e}")  # Debugging
            self.show_message(f"Ошибка при обновлении статуса: {str(e)}")

    def _on_status_update_success(self, result):
        print(f"Status update success: {result}")
        if 'new_token' in result and self.auth_controller:
            self.auth_controller.token = result['new_token']

        history_view = self.sm.get_screen('history')
        if hasattr(history_view, 'update_invoice_in_list'):
            history_view.update_invoice_in_list(result)

        self.show_message("Статус оплаты обновлен")

    def _on_status_update_error(self, error):
        self.show_message(f"Ошибка при обновлении статуса: {error}")
        self.payment_status_value = 1 if self.payment_status_value == 0 else 0
        self.payment_button.text = 'Оплачено!' if self.payment_status_value == 1 else 'Не оплачено!'

    def clear_form(self):
        self.editing_invoice = None
        self.clear_invoice_form()

    def save_invoice(self) -> None:
        try:
            invoice_data = self._collect_invoice_data()
        except ValueError as e:
            self.show_message(str(e))
            return
        if not invoice_data["contact"]:
            self.show_message("Ошибка: не указан контакт")
            return
        if not invoice_data["items"]:
            self.show_message("Ошибка: добавьте хотя бы одну позицию в накладную")
            return

        if self.editing_invoice:
            self.api_controller.update_invoice(
                self.editing_invoice,
                invoice_data,
                success_callback=self.on_save_success,
            )
        else:
            self.api_controller.create_invoice(
                invoice_data,
                success_callback=self.on_save_success,
            )

    def on_save_success(self, result):
        if 'new_token' in result and self.auth_controller:
            self.auth_controller.token = result['new_token']

        self.show_message("Накладная успешно сохранена")

        history_view = self.sm.get_screen('history')

        new_invoice_data = {
            'number': str(self.displayed_text),
            'date': result.get('created_at', '').split('T')[0],
            'contact': result.get('contact_info', ''),
            'total': result.get('total_amount', 0.0),
            'is_paid': result.get('is_paid', False)
        }

        if hasattr(history_view, 'ids') and hasattr(history_view.ids, 'invoice_list'):
            current_data = history_view.ids.invoice_list.data
            history_view.ids.invoice_list.data = [new_invoice_data] + current_data
        self.clear_invoice_form()
        self.sm.current = 'history'

    def add_initial_rows(self, count: int = 10) -> None:
        for _ in range(count):
            self.add_row()

    def add_row(self) -> None:
        table_row = InvoiceTable()
        row_count = len(self.table_content.children) + 1
        table_row.number_label.text = str(row_count)
        table_row.bind_total_update(self.update_total)
        self.table_content.add_widget(table_row)
        self.update_total()

    def del_row(self) -> None:
        if not self.table_content.children:
            return

        self.table_content.remove_widget(self.table_content.children[0])
        self._renumber_rows()
        self.update_total()

    def _renumber_rows(self) -> None:
        for i, row in enumerate(reversed(self.table_content.children), 1):
            row.number_label.text = str(i)

    def update_total(self, *args) -> None:
        total = sum(child.total_sum() for child in self.table_content.children)
        self.total_sum_label.text = f'{total:.2f}'

    def calculate_total(self) -> float:
        try:
            return float(self.total_sum_label.text)
        except ValueError:
            return 0.0

    def update_date_time(self) -> None:
        current_time = datetime.now()
        rounded_time = current_time.replace(second=0, microsecond=0)
        if current_time.second >= 30:
            rounded_time += timedelta(minutes=1)
        self.date_label.text = rounded_time.strftime("%Y-%m-%d")
        print(f"Updated date: {self.date_label.text}")  # Debugging

    def payment_status(self) -> None:
        if self.payment_status_value == 0:
            self.payment_button.text = 'Оплачено!'
            self.payment_status_value = 1
        else:
            self.payment_button.text = 'Не оплачено!'
            self.payment_status_value = 0

        if self.editing_invoice:
            self.update_invoice_status()
