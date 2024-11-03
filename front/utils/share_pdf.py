# utils/share_manager.py
from kivy.utils import platform
import subprocess
import webbrowser
from urllib.parse import quote
import os
from plyer import email
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label


class ShareManager:
    def __init__(self):
        self.platform = platform

    def open_file_location(self, file_path):
        """Открывает папку с файлом"""
        try:
            folder_path = os.path.dirname(file_path)
            if self.platform == 'win':
                os.startfile(folder_path)
            elif self.platform == 'macosx':
                subprocess.call(['open', folder_path])
            else:
                subprocess.call(['xdg-open', folder_path])
        except Exception as e:
            print(f"Error opening file location: {e}")

    def share_via_email(self, file_path):
        """Показывает диалог для отправки email"""
        try:
            content = BoxLayout(orientation='vertical', spacing=10, padding=10)

            # Поле для email
            email_layout = BoxLayout(size_hint_y=None, height='40dp')
            email_layout.add_widget(Label(text='Email:', size_hint_x=0.3))
            email_input = TextInput(multiline=False)
            email_layout.add_widget(email_input)
            content.add_widget(email_layout)

            # Кнопки действий
            buttons_layout = BoxLayout(size_hint_y=None, height='40dp', spacing=10)

            def send_email(instance):
                recipient = email_input.text
                if recipient:
                    try:
                        email.send(
                            recipient=recipient,
                            subject="Накладная",
                            text="Во вложении находится накладная",
                            attach=file_path
                        )
                    except Exception as e:
                        print(f"Error sending email: {e}")
                        # Fallback - открываем почтовый клиент
                        mailto = f"mailto:{recipient}?subject={quote('Накладная')}"
                        webbrowser.open(mailto)
                popup.dismiss()

            send_button = Button(text='Отправить')
            send_button.bind(on_release=send_email)
            buttons_layout.add_widget(send_button)

            cancel_button = Button(text='Отмена')
            cancel_button.bind(on_release=lambda x: popup.dismiss())
            buttons_layout.add_widget(cancel_button)

            content.add_widget(buttons_layout)

            popup = Popup(
                title='Отправить по email',
                content=content,
                size_hint=(None, None),
                size=(400, 200),
                auto_dismiss=False
            )
            popup.open()

        except Exception as e:
            print(f"Error preparing email dialog: {e}")

    def share_via_messenger(self, file_path, messenger_type='whatsapp'):
        """Открывает мессенджер для отправки файла"""
        try:
            content = BoxLayout(orientation='vertical', spacing=10, padding=10)

            # Поле для номера телефона
            phone_layout = BoxLayout(size_hint_y=None, height='40dp')
            phone_layout.add_widget(Label(text='Телефон:', size_hint_x=0.3))
            phone_input = TextInput(multiline=False)
            phone_layout.add_widget(phone_input)
            content.add_widget(phone_layout)

            # Кнопки действий
            buttons_layout = BoxLayout(size_hint_y=None, height='40dp', spacing=10)

            def open_messenger(instance):
                phone = phone_input.text.strip().replace('+', '')
                if phone:
                    if messenger_type == 'whatsapp':
                        url = f"https://wa.me/{phone}?text={quote('Накладная во вложении')}"
                    else:  # telegram
                        url = f"tg://msg?to={phone}&text={quote('Накладная во вложении')}"
                    webbrowser.open(url)
                popup.dismiss()

            send_button = Button(text='Открыть')
            send_button.bind(on_release=open_messenger)
            buttons_layout.add_widget(send_button)

            cancel_button = Button(text='Отмена')
            cancel_button.bind(on_release=lambda x: popup.dismiss())
            buttons_layout.add_widget(cancel_button)

            content.add_widget(buttons_layout)

            popup = Popup(
                title=f'Отправить через {"WhatsApp" if messenger_type == "whatsapp" else "Telegram"}',
                content=content,
                size_hint=(None, None),
                size=(400, 200),
                auto_dismiss=False
            )
            popup.open()

        except Exception as e:
            print(f"Error preparing messenger dialog: {e}")

    def show_share_popup(self, file_path):
        """Показывает основное меню отправки"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        buttons = [
            ('Открыть папку с файлом', lambda x: self.open_file_location(file_path)),
            ('Отправить по email', lambda x: self.share_via_email(file_path)),
            ('Отправить через WhatsApp', lambda x: self.share_via_messenger(file_path, 'whatsapp')),
            ('Отправить через Telegram', lambda x: self.share_via_messenger(file_path, 'telegram'))
        ]

        for text, callback in buttons:
            btn = Button(
                text=text,
                size_hint_y=None,
                height='48dp'
            )
            btn.bind(on_release=callback)
            content.add_widget(btn)

        close_button = Button(
            text='Закрыть',
            size_hint_y=None,
            height='48dp'
        )

        popup = Popup(
            title='Отправить накладную',
            content=content,
            size_hint=(None, None),
            size=(400, 400)
        )

        close_button.bind(on_release=popup.dismiss)
        content.add_widget(close_button)

        popup.open()