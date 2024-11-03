# views/main_view.py
from kivy.uix.screenmanager import Screen



class MainView(Screen):
    def __init__(self, screen_manager):
        super().__init__(name='main')
        self.sm = screen_manager
        self.sm.add_widget(self)

    def show_create_invoice(self):
        self.sm.current = 'invoice'

    def show_history(self):
        self.sm.current = 'history'

    def show_analytics(self):
        self.sm.current = 'analytics'

    def logout(self):
        self.sm.current = 'auth'
