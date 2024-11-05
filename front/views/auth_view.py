# views/auth_view.py
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty


class AuthView(Screen):
    auth_controller = ObjectProperty(None)  # Добавляем как свойство

    def __init__(self, screen_manager, **kwargs):
        super().__init__(name='auth', **kwargs)
        self.sm = screen_manager
        self.sm.add_widget(self)

    def show_message(self, message):
        popup = Popup(
            title='Сообщение',
            content=Label(text=message),
            size_hint=(None, None),
            size=(400, 200)
        )
        popup.open()

    def on_login_success(self, result):
        if self.auth_controller:
            self.auth_controller.token = result.get('access_token')
            print(f"Token received: {self.auth_controller.token}")  # Отладка
            for screen in self.sm.screens:
                if hasattr(screen, 'auth_controller'):
                    screen.auth_controller = self.auth_controller
                    if hasattr(screen, 'on_auth_controller'):
                        screen.on_auth_controller(screen, self.auth_controller)

        self.sm.current = 'main'

    def on_login_error(self, error):
        self.show_message(f"Ошибка авторизации: {error}")

    def login(self, username, password):
        """Обработчик входа"""
        if not username or not password:
            self.show_message("Пожалуйста, введите логин и пароль")
            return

        self.auth_controller.login(
            username=username,
            password=password,
            success_callback=self.on_login_success,
            error_callback=self.on_login_error
        )
    def on_register_success(self, result):
        self.show_message("Регистрация успешна!")
        self.sm.current = 'main'

    def on_register_error(self, error):
        self.show_message(f"Ошибка регистрации: {error}")

    def register(self, login, email, password, phone):
        user_data = {
            "login": login,
            "email": email,
            "password": password,
            "phone": phone
        }

        self.auth_controller.register(
            user_data=user_data,
            success_callback=self.on_register_success,
            error_callback=self.on_register_error
        )

    def show_registration(self):
        self.show_message("Функция регистрации находится в разработке")

    def show_password_recovery(self):

        self.show_message("Функция восстановления пароля находится в разработке")