# views/invoice_table.py
from kivy.uix.boxlayout import BoxLayout
from typing import Optional, Callable


class InvoiceTable(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Кэшируем ссылки на элементы интерфейса
        self.name_input = self.ids.name
        self.quantity_input = self.ids.quantity
        self.price_input = self.ids.price
        self.sum_label = self.ids.sum
        self.number_label = self.ids.number

        self.bind_row_calculations()

    def bind_row_calculations(self) -> None:
        """Привязка изменений количества и цены к пересчету суммы."""
        self.quantity_input.bind(text=self.calculate_row_sum)
        self.price_input.bind(text=self.calculate_row_sum)

    def bind_total_update(self, callback: Callable) -> None:
        """Привязка изменений количества и цены к обновлению общей суммы."""
        self.quantity_input.bind(text=callback)
        self.price_input.bind(text=callback)

    def calculate_row_sum(self, instance: Optional[object] = None, value: Optional[str] = None) -> None:
        """Вычисление суммы строки на основе количества и цены."""
        try:
            quantity = float(self.quantity_input.text)
            price = float(self.price_input.text)
            total = quantity * price
            self.sum_label.text = f'{total:.2f}'
        except ValueError:
            self.sum_label.text = '0.00'

    def total_sum(self) -> float:
        """Возвращает сумму строки как float."""
        try:
            return float(self.sum_label.text)
        except ValueError:
            return 0.0

    def reset_values(self) -> None:
        """Сброс значений полей строки."""
        self.name_input.text = ""
        self.quantity_input.text = ''
        self.price_input.text = ''
        self.quantity_input.hint_text = '0.0'
        self.price_input.hint_text = '0.0'
        self.calculate_row_sum()
