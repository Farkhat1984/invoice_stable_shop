# views/invoice_history_item.py
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.app import App


class InvoiceItemWidget(BoxLayout):
    number = StringProperty('')
    date = StringProperty('')
    contact = StringProperty('')
    total = NumericProperty(0.0)
    is_paid = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Кэшируем ссылки на элементы интерфейса, если необходимо
        # Например:
        # self.edit_button = self.ids.edit_button
        # self.delete_button = self.ids.delete_button

    def edit_invoice(self, instance) -> None:
        """Редактирование накладной."""
        try:
            # Получаем ScreenManager
            app = App.get_running_app()
            screen_manager = app.root

            # Получаем экран истории
            history_view = screen_manager.get_screen('history')

            if history_view:
                print(f"Editing invoice {self.number}")  # Отладка
                history_view.edit_invoice(int(self.number))
            else:
                raise ValueError("History view not found")
        except Exception as e:
            print(f"Error in edit_invoice: {e}")  # Отладка
            self.show_error_popup(f"Ошибка при редактировании: {str(e)}")

    def delete_invoice(self, instance) -> None:
        """Удаление накладной с подтверждением."""
        try:
            # Создаем popup для подтверждения удаления
            content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            content.add_widget(Label(text=f'Вы уверены, что хотите удалить накладную {self.number}?'))

            buttons = BoxLayout(size_hint_y=None, height=40, spacing=10)
            confirm_btn = Button(text='Удалить', background_color=[1, 0.3, 0.3, 1])
            cancel_btn = Button(text='Отмена')

            confirm_btn.bind(on_press=lambda x: self.confirm_delete(x, content))
            cancel_btn.bind(on_press=lambda x: self.cancel_delete(x, content))

            buttons.add_widget(confirm_btn)
            buttons.add_widget(cancel_btn)
            content.add_widget(buttons)

            self.popup = Popup(
                title='Подтверждение удаления',
                content=content,
                size_hint=(None, None),
                size=(400, 200),
                auto_dismiss=False
            )
            self.popup.open()
        except Exception as e:
            print(f"Error in delete_invoice: {e}")  # Отладка
            self.show_error_popup(f"Ошибка при удалении: {str(e)}")

    def confirm_delete(self, instance, content) -> None:
        """Подтверждение удаления накладной."""
        try:
            app = App.get_running_app()
            screen_manager = app.root
            history_view = screen_manager.get_screen('history')

            if history_view:
                print(f"Deleting invoice {self.number}")  # Отладка
                history_view.delete_invoice(int(self.number))
                self.popup.dismiss()
            else:
                raise ValueError("History view not found")
        except Exception as e:
            print(f"Error in confirm_delete: {e}")  # Отладка
            self.show_error_popup(f"Ошибка при удалении: {str(e)}")

    def cancel_delete(self, instance, content) -> None:
        """Отмена удаления накладной."""
        try:
            self.popup.dismiss()
        except Exception as e:
            print(f"Error in cancel_delete: {e}")  # Отладка
            self.show_error_popup(f"Ошибка при отмене удаления: {str(e)}")

    def show_error_popup(self, message: str) -> None:
        """Показ сообщения об ошибке."""
        popup = Popup(
            title='Ошибка',
            content=Label(text=message),
            size_hint=(None, None),
            size=(400, 200)
        )
        popup.open()
