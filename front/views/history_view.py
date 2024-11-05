from kivy.factory import Factory
from front.views.invoice_history_item import InvoiceItemWidget
from kivy.uix.screenmanager import Screen
from front.controllers.history_api_controller import HistoryAPIController
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from front.utils.date_picker import CustomDatePicker as DatePicker
from kivy.clock import Clock

Factory.register('InvoiceItemWidget', InvoiceItemWidget)


class HistoryView(Screen):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(name='history', **kwargs)
        self.sm = screen_manager
        self.sm.add_widget(self)
        self.api_controller: HistoryAPIController = None
        self.original_data: List[Dict[str, Any]] = []
        self.current_data: List[Dict[str, Any]] = []
        self.sort_field: str = 'date'
        self.sort_reverse: bool = True
        self.current_grouping: str = None
        self.is_active = False
        self.current_shop_id = None
        self.last_invoice_id = None

        # Cache UI elements
        self._cache_ui_elements()

    def _cache_ui_elements(self):
        self.invoice_number_filter = self.ids.invoice_number_filter
        self.date_from_filter = self.ids.date_from
        self.date_to_filter = self.ids.date_to
        self.contact_filter = self.ids.contact_filter
        self.amount_from_filter = self.ids.amount_from
        self.amount_to_filter = self.ids.amount_to
        self.payment_status_filter = self.ids.payment_status
        self.invoice_list = self.ids.invoice_list

    def on_enter(self):
        self.is_active = True
        Clock.schedule_once(lambda dt: self.refresh_list(), 0.1)
        if self.api_controller:
            self.load_invoice_stats()

    def on_leave(self):
        self.is_active = False

    def load_invoice_stats(self) -> None:
        if not self.api_controller:
            return

        def on_stats_success(stats):
            pass

        def on_stats_error(error):
            print(f"Error loading stats: {error}")

        self.api_controller.get_invoice_stats(
            shop_id=self.current_shop_id,
            success_callback=on_stats_success,
            error_callback=on_stats_error
        )

    def reset_filters(self) -> None:
        self.invoice_number_filter.text = ''
        self.date_from_filter.text = ''
        self.date_to_filter.text = ''
        self.contact_filter.text = ''
        self.amount_from_filter.text = ''
        self.amount_to_filter.text = ''
        self.payment_status_filter.text = 'Все'
        self.current_data = self.original_data.copy()
        Clock.schedule_once(lambda dt: self.update_display(), 0.1)

    def show_date_picker_from(self, instance):
        date_picker = DatePicker(callback=self.set_date_from)
        date_picker.open()

    def show_date_picker_to(self, instance):
        date_picker = DatePicker(callback=self.set_date_to)
        date_picker.open()

    def set_date_from(self, date_str):
        self.date_from_filter.text = date_str

    def set_date_to(self, date_str):
        self.date_to_filter.text = date_str

    def validate_date_range(self):
        if not self.date_from_filter.text or not self.date_to_filter.text:
            return True

        try:
            date_from = datetime.strptime(self.date_from_filter.text, "%Y-%m-%d")
            date_to = datetime.strptime(self.date_to_filter.text, "%Y-%m-%d")

            if date_from > date_to:
                self.show_message("Дата 'с' не может быть позже даты 'по'")
                return False

            if date_to - date_from > timedelta(days=365):
                self.show_message("Диапазон дат не может превышать один год")
                return False

            return True
        except ValueError:
            self.show_message("Неверный формат даты")
            return False

    def sort_invoices(self, field: str) -> None:
        if self.sort_field == field:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_field = field
            self.sort_reverse = False

        try:
            if field == 'total':
                self.current_data.sort(key=lambda x: float(x.get(field, 0.0)), reverse=self.sort_reverse)
            elif field == 'date':
                self.current_data.sort(key=lambda x: datetime.strptime(x.get(field, ''), "%Y-%m-%d"),
                                     reverse=self.sort_reverse)
            elif field == 'number':
                # Convert invoice number to integer for proper numeric sorting
                self.current_data.sort(key=lambda x: int(x.get(field, '0')), reverse=self.sort_reverse)
            else:
                self.current_data.sort(key=lambda x: x.get(field, '').lower(), reverse=self.sort_reverse)
            Clock.schedule_once(lambda dt: self.update_display(), 0.1)
        except Exception as e:
            self.show_message(f"Ошибка при сортировке: {str(e)}")

    def group_invoices(self, field: str) -> None:
        if not self.current_data:
            return

        self.current_grouping = field
        grouped_data = {}

        for invoice in self.current_data:
            key = invoice.get(field, 'Не указано')
            grouped_data.setdefault(key, []).append(invoice)

        display_data = []
        for key, group in sorted(grouped_data.items(), key=lambda x: x[0]):
            header_text = 'Оплачено' if key and field == 'is_paid' else 'Не оплачено' if field == 'is_paid' else str(
                key)
            total_amount = sum(float(inv.get('total', 0.0)) for inv in group)
            display_data.append({
                'is_group_header': True,
                'number': '',
                'date': '',
                'contact': f"{header_text} ({len(group)} шт.)",
                'total': f"{total_amount:.2f}",
                'is_paid': all(inv.get('is_paid', False) for inv in group)
            })
            display_data.extend(group)

        self.invoice_list.data = display_data
        self.invoice_list.refresh_from_data()

    def clear_grouping(self) -> None:
        self.current_grouping = None
        Clock.schedule_once(lambda dt: self.update_display(), 0.1)

    def _convert_invoice_to_display_format(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'number': str(invoice.get('id', '')),
            'date': invoice.get('created_at', '').split('T')[0] if 'T' in invoice.get('created_at', '')
            else invoice.get('created_at', ''),
            'contact': invoice.get('contact_info', ''),
            'total': f"{float(invoice.get('total_amount', 0.0)):.2f}",
            'is_paid': invoice.get('is_paid', False),
            'shop_id': invoice.get('shop_id', self.current_shop_id)  # Include shop_id
        }

    def update_display(self) -> None:
        if not self.is_active:
            return

        if self.current_grouping:
            self.group_invoices(self.current_grouping)
        else:
            self.invoice_list.data = self.current_data
            self.invoice_list.refresh_from_data()

    def edit_invoice(self, invoice_id: int) -> None:
        try:
            print(f"HistoryView: Loading invoice {invoice_id} for editing")

            def on_invoice_loaded(invoice_data: Dict[str, Any]):
                try:
                    print(f"HistoryView: Invoice data loaded: {invoice_data}")
                    invoice_view: Screen = self.sm.get_screen('invoice')
                    if invoice_view:
                        invoice_view.load_invoice_data(invoice_data)
                        self.sm.current = 'invoice'
                    else:
                        raise ValueError("Invoice view not found")
                except Exception as e:
                    print(f"Error in on_invoice_loaded: {e}")
                    self.show_message(f"Ошибка при загрузке данных накладной: {str(e)}")

            if self.api_controller:
                self.api_controller.get_invoice_details(
                    invoice_id,
                    success_callback=on_invoice_loaded,
                    error_callback=lambda error: self.show_message(f"Ошибка загрузки накладной: {error}")
                )
            else:
                raise ValueError("API controller not initialized")

        except Exception as e:
            print(f"Error in edit_invoice: {e}")
            self.show_message(f"Ошибка при редактировании накладной: {str(e)}")

    def on_invoices_loaded(self, result: List[Dict[str, Any]]) -> None:
        """Callback for successful invoice load."""
        try:
            invoice_data = [self._convert_invoice_to_display_format(invoice) for invoice in result]

            # Update last_invoice_id if available
            if result and self.auth_controller:
                latest_id = max(int(invoice.get('id', 0)) for invoice in result)
                self.last_invoice_id = latest_id
                self.auth_controller.last_invoice_id = latest_id

            self.original_data = invoice_data.copy()
            self.current_data = invoice_data.copy()

            Clock.schedule_once(lambda dt: self.update_display(), 0.1)

        except Exception as e:
            print(f"Error in on_invoices_loaded: {e}")
            self.show_message(f"Ошибка обработки данных накладных: {str(e)}")

    def on_auth_controller(self, instance, value) -> None:
        """Set up API controller when auth_controller changes."""
        if value:
            print(f"HistoryView: Setting auth_controller with token: {value.token}")
            self.api_controller = HistoryAPIController(auth_controller=value)
            self.current_shop_id = getattr(value, 'current_shop_id', None)
            self.last_invoice_id = getattr(value, 'last_invoice_id', None)

            if value.token:
                print("HistoryView: Token present, loading invoices")
                Clock.schedule_once(lambda dt: self.refresh_list(), 0.1)
            else:
                print("HistoryView: No token available")

    def update_invoice_in_list(self, updated_invoice: Dict[str, Any]) -> None:
        try:
            invoice_number = str(updated_invoice.get('id'))
            invoice_data = self._convert_invoice_to_display_format(updated_invoice)
            for data_list in [self.original_data, self.current_data]:
                for i, invoice in enumerate(data_list):
                    if invoice['number'] == invoice_number:
                        data_list[i] = invoice_data.copy()
                        break

            Clock.schedule_once(lambda dt: self.update_display(), 0.1)

        except Exception as e:
            print(f"Error in update_invoice_in_list: {e}")
            self.show_message(f"Ошибка при обновлении накладной: {str(e)}")

    def remove_invoice_from_list(self, invoice_id: int) -> None:
        try:
            invoice_id_str = str(invoice_id)

            if str(self.last_invoice_id) == invoice_id_str:
                self.last_invoice_id = None
                if self.auth_controller:
                    self.auth_controller.last_invoice_id = None

            self.original_data = [inv for inv in self.original_data if inv['number'] != invoice_id_str]
            self.current_data = [inv for inv in self.current_data if inv['number'] != invoice_id_str]
            Clock.schedule_once(lambda dt: self.update_display(), 0.1)
        except Exception as e:
            print(f"Error in remove_invoice_from_list: {e}")
            self.show_message(f"Ошибка при удалении накладной: {str(e)}")

    def add_invoice_to_list(self, new_invoice: Dict[str, Any]) -> None:
        try:
            invoice_data = self._convert_invoice_to_display_format(new_invoice)
            if new_invoice.get('id'):
                self.last_invoice_id = int(new_invoice['id'])
                if self.auth_controller:
                    self.auth_controller.last_invoice_id = self.last_invoice_id

            self.original_data.insert(0, invoice_data.copy())
            self.current_data.insert(0, invoice_data.copy())

            Clock.schedule_once(lambda dt: self.update_display(), 0.1)

        except Exception as e:
            print(f"Error in add_invoice_to_list: {e}")
            self.show_message(f"Ошибка при добавлении накладной: {str(e)}")

    def show_message(self, message: str) -> None:
        popup = Popup(
            title='Сообщение',
            content=Label(text=message),
            size_hint=(None, None),
            size=(400, 200)
        )
        popup.open()

    def on_load_error(self, error: str) -> None:
        print(f"HistoryView: Load error: {error}")
        self.show_message(f"Ошибка загрузки накладных: {error}")

    def search_invoices(self, instance=None) -> None:
        if not self.validate_date_range():
            return

        try:
            filtered_data = [
                invoice for invoice in self.original_data
                if invoice.get('shop_id', self.current_shop_id) == self.current_shop_id
            ]

            if self.invoice_number_filter.text:
                search_number = self.invoice_number_filter.text.strip().lower()
                filtered_data = [
                    invoice for invoice in filtered_data
                    if search_number in invoice['number'].lower()
                ]

            if self.date_from_filter.text:
                date_from = datetime.strptime(self.date_from_filter.text, "%Y-%m-%d")
                filtered_data = [
                    invoice for invoice in filtered_data
                    if datetime.strptime(invoice['date'], "%Y-%m-%d") >= date_from
                ]

            if self.date_to_filter.text:
                date_to = datetime.strptime(self.date_to_filter.text, "%Y-%m-%d")
                filtered_data = [
                    invoice for invoice in filtered_data
                    if datetime.strptime(invoice['date'], "%Y-%m-%d") <= date_to
                ]

            if self.contact_filter.text:
                search_contact = self.contact_filter.text.strip().lower()
                filtered_data = [
                    invoice for invoice in filtered_data
                    if search_contact in invoice['contact'].lower()
                ]

            if self.amount_from_filter.text:
                min_amount = float(self.amount_from_filter.text)
                filtered_data = [
                    invoice for invoice in filtered_data
                    if float(invoice['total']) >= min_amount
                ]

            if self.amount_to_filter.text:
                max_amount = float(self.amount_to_filter.text)
                filtered_data = [
                    invoice for invoice in filtered_data
                    if float(invoice['total']) <= max_amount
                ]

            if self.payment_status_filter.text != 'Все':
                is_paid = self.payment_status_filter.text == 'Оплачено'
                filtered_data = [
                    invoice for invoice in filtered_data
                    if invoice['is_paid'] == is_paid
                ]

            self.current_data = filtered_data
            Clock.schedule_once(lambda dt: self.update_display(), 0.1)

        except Exception as e:
            print(f"Error in search_invoices: {e}")
            self.show_message(f"Ошибка при фильтрации данных: {str(e)}")

    def refresh_list(self, instance=None) -> None:
        if not self.api_controller:
            print("HistoryView: No API controller")
            self.show_message("API контроллер не инициализирован")
            return

        if not hasattr(self.sm.get_screen('invoice'), 'auth_controller') or \
                not self.sm.get_screen('invoice').auth_controller or \
                not self.sm.get_screen('invoice').auth_controller.token:
            print("HistoryView: No auth token")
            self.show_message("Необходима авторизация для обновления списка накладных")
            return

        print(f"HistoryView: Refreshing list with token: {self.sm.get_screen('invoice').auth_controller.token}")

        filters = {'shop_id': self.current_shop_id} if self.current_shop_id else {}

        self.api_controller.get_invoices(
            success_callback=self.on_invoices_loaded,
            error_callback=self.on_load_error,
            filters=filters
        )

        self.load_invoice_stats()

    def delete_invoice(self, invoice_id: int) -> None:
        try:
            def on_delete_success():
                if self.last_invoice_id == invoice_id:
                    self.last_invoice_id = None
                    if self.auth_controller:
                        self.auth_controller.last_invoice_id = None

                self.show_message("Накладная успешно удалена")
                self.refresh_list()
                invoice_view = self.sm.get_screen('invoice')
                if hasattr(invoice_view, '_update_invoice_number'):
                    invoice_view._update_invoice_number()

            def on_delete_error(error: str):
                self.show_message(f"Ошибка удаления накладной: {error}")

            if self.api_controller:
                self.api_controller.delete_invoice(
                    invoice_id,
                    success_callback=on_delete_success,
                    error_callback=on_delete_error
                )
            else:
                self.show_message("API контроллер не инициализирован")
        except Exception as e:
            print(f"Error in delete_invoice: {e}")
            self.show_message(f"Ошибка при удалении накладной: {str(e)}")

    def apply_filters(self, filters: Dict[str, Any]) -> None:
        try:
            if self.current_shop_id:
                filters['shop_id'] = self.current_shop_id
            self.api_controller.get_invoices(
                success_callback=self.on_invoices_loaded,
                error_callback=self.on_load_error,
                filters=filters
            )
        except Exception as e:
            print(f"Error applying filters: {e}")
            self.show_message(f"Ошибка при применении фильтров: {str(e)}")