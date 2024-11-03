# views/analytics_view.py
from kivy.uix.screenmanager import Screen


class AnalyticsView(Screen):
    def __init__(self, screen_manager):
        super().__init__(name='analytics')
        self.sm = screen_manager
        self.sm.add_widget(self)
