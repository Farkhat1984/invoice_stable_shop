from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock

from controllers.auth_controller import logger
from front.controllers.main_api_controller import MainViewApiController


class MainView(Screen):
    auth_controller = ObjectProperty(None)


    def __init__(self, screen_manager, **kwargs):
        super().__init__(name='main', **kwargs)
        self.sm = screen_manager
        self.sm.add_widget(self)
        self.api_controller = None
        Clock.schedule_once(self._initialize_view)

    def on_auth_controller(self, instance, value):
        if value and value.token:
            self.api_controller = MainViewApiController(
                auth_controller=value,
                base_url="http://localhost:8000"
            )
        else:
            pass

    def _initialize_view(self, dt):
        pass

    def show_create_invoice(self):
        if not self.api_controller:
            logger.error("API controller not initialized")
            return

        def success_callback(next_number):
            second_screen = self.manager.get_screen('invoice')
            second_screen.displayed_text = f"{next_number}"
            self.sm.current = 'invoice'

        def error_callback(error_msg):
            logger.error(f"Failed to get next invoice number: {error_msg}")
            second_screen = self.manager.get_screen('invoice')
            second_screen.displayed_text = "Ошибка получения номера счета"
            self.sm.current = 'invoice'

        self.api_controller.get_next_invoice_number(
            success_callback=success_callback,
            error_callback=error_callback
        )

    def show_history(self):
        self.sm.current = 'history'

    def show_analytics(self):
        self.sm.current = 'analytics'

    def logout(self):
        if self.auth_controller:
            self.auth_controller.token = None
            self.api_controller = None
        self.sm.current = 'auth'