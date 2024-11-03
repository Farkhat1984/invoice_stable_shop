from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.metrics import dp
from front.views.analytics_view import AnalyticsView
from front.views.auth_view import AuthView
from front.views.history_view import HistoryView
from front.views.main_view import MainView
from front.views.invoice_view import InvoiceView
from front.controllers.auth_controller import AuthAPIController


class InvoiceApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Установка минимальных размеров
        Window.minimum_width = 600
        Window.minimum_height = 1000
        Window.max_width = 700
        Window.max_height = 1150

        # Установка начального размера равного минимальному
        Window.size = (Window.minimum_width, Window.minimum_height)

        # Оптимизация DPI
        Window.density = 1.5
        Window.dpi = 160

        Window.allow_screensaver = True
        Window.softinput_mode = 'pan'
        Window.rotation = 0

    def build(self):

        Builder.load_file('views/kv_view/styles.kv')
        Builder.load_file('views/kv_view/date_picker.kv')
        Builder.load_file('views/kv_view/invoice_table.kv')
        Builder.load_file('views/kv_view/invoice_history_item.kv')
        Builder.load_file('views/kv_view/auth.kv')
        Builder.load_file('views/kv_view/main.kv')
        Builder.load_file('views/kv_view/invoice.kv')
        Builder.load_file('views/kv_view/history.kv')
        Builder.load_file('views/kv_view/analytics.kv')

        sm = ScreenManager()
        auth_controller = AuthAPIController()

        auth_view = AuthView(sm)
        auth_view.auth_controller = auth_controller

        MainView(sm)

        invoice_view = InvoiceView(sm)
        invoice_view.auth_controller = auth_controller

        history_view = HistoryView(sm)
        history_view.auth_controller = auth_controller

        AnalyticsView(sm)

        return sm


if __name__ == '__main__':
    InvoiceApp().run()