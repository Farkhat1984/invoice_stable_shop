from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from datetime import datetime
import calendar
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.factory import Factory


class CustomDatePicker(Popup):
    calendar_grid = ObjectProperty(None)
    month_year_label = ObjectProperty(None)
    current_month = NumericProperty()
    current_year = NumericProperty()
    current_day = NumericProperty()
    selected_date = StringProperty()

    def __init__(self, callback, **kwargs):
        today = datetime.now()
        self.current_month = today.month
        self.current_year = today.year
        self.current_day = today.day
        self.callback = callback
        super(CustomDatePicker, self).__init__(**kwargs)
        self.setup_calendar()

    def setup_calendar(self):
        weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        weekday_grid = self.ids.weekdays
        default_color = (1, 1, 1, 1)

        for day in weekdays:
            weekday_grid.add_widget(Factory.CalendarDayLabel(
                text=day,
                color=getattr(self, 'title_color', default_color)
            ))
        self.update_calendar()

    def get_month_year_text(self):
        months = {
            1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
            5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
            9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
        }
        return f"{months[self.current_month]} {self.current_year}"

    def update_calendar(self):
        if not hasattr(self, 'ids') or 'calendar_grid' not in self.ids:
            return

        self.ids.calendar_grid.clear_widgets()
        self.ids.month_year_label.text = self.get_month_year_text()

        # Получаем календарь на текущий месяц
        cal = calendar.monthcalendar(self.current_year, self.current_month)

        for week in cal:
            for day in week:
                if day == 0:
                    # Пустая ячейка
                    btn = Factory.CalendarDayLabel(
                        text='',
                        size_hint_y=None,
                        height=dp(35)
                    )
                else:
                    # Кнопка с днём
                    btn = Factory.CalendarButton(
                        text=str(day),
                        size_hint_y=None,
                        height=dp(35)
                    )

                    # Выделяем текущий день
                    if (day == datetime.now().day and
                            self.current_month == datetime.now().month and
                            self.current_year == datetime.now().year):
                        btn.background_color = (0.3, 0.7, 1, 1)

                    # Создаем замыкание для корректной привязки дня
                    def create_callback(day_value):
                        return lambda instance: self.select_date(day_value)

                    btn.bind(on_release=create_callback(day))

                self.ids.calendar_grid.add_widget(btn)

    def select_date(self, day):
        selected_date = datetime(self.current_year, self.current_month, day)
        formatted_date = selected_date.strftime('%Y-%m-%d')
        self.callback(formatted_date)
        self.dismiss()

    def set_today(self, instance):
        today = datetime.now()
        formatted_date = today.strftime('%Y-%m-%d')
        self.callback(formatted_date)
        self.dismiss()

    def prev_month(self, instance):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.update_calendar()

    def next_month(self, instance):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.update_calendar()