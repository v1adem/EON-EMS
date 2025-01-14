import asyncio
import time

from AsyncioPySide6 import AsyncioPySide6
from PySide6 import QtAsyncio
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from tortoise.exceptions import IntegrityError

from models.Admin import Admin


class RegistrationLoginForm(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)

        self.main_window = main_window

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center_layout = QHBoxLayout()

        form_layout = QVBoxLayout()

        self.status_label = QLabel(self)
        self.setStyleSheet("font-size: 18px;")
        form_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.username_label = QLabel("Логін:", self)
        self.username_input = QLineEdit(self)
        form_layout.addWidget(self.username_label)
        form_layout.addWidget(self.username_input)

        self.password_label = QLabel("Пароль:", self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self.password_label)
        form_layout.addWidget(self.password_input)

        self.login_button = QPushButton("Вхід")
        self.login_button.clicked.connect(self.login)
        self.register_button = QPushButton("Реєстрація")
        self.register_button.clicked.connect(self.register)
        self.guest_button = QPushButton("Ввійти як гість")
        self.guest_button.clicked.connect(self.guest_login)

        form_layout.addWidget(self.login_button)
        form_layout.addWidget(self.register_button)
        form_layout.addWidget(self.guest_button)

        AsyncioPySide6.runTask(self.check_if_first_run())


        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        form_widget.setFixedWidth(self.main_window.width() // 3)

        form_widget.setStyleSheet("font-size: 18px;")

        center_layout.addWidget(form_widget)

        main_layout.addLayout(center_layout)

        main_layout.setSpacing(10)

    async def check_if_first_run(self):
        try:
            admin = await Admin.first()
            if admin:
                self.show_login_form()
            else:
                self.show_registration_form()
        except Exception as e:
            print(f"Error checking if first run: {e}")

    def show_registration_form(self):
        self.status_label.setText("Будь ласка, зареєструйтеся")
        self.register_button.setVisible(True)
        self.login_button.setVisible(False)
        self.guest_button.setVisible(False)

    def show_login_form(self):
        self.status_label.setText("Введіть логін та пароль")
        self.register_button.setVisible(False)
        self.login_button.setVisible(True)
        self.guest_button.setVisible(True)

    def register(self):
        async def run_register():
            username = self.username_input.text()
            password = self.password_input.text()
            admin = await Admin(username=username, password=password)
            try:
                await admin.save()
                self.status_label.setText("Реєстрація успішна!")
                await asyncio.sleep(2)
                self.show_login_form()
            except IntegrityError:
                self.status_label.setText("Цей користувач вже існує!")

        AsyncioPySide6.runTask(run_register())

    def login(self):
        async def run_login():
            username = self.username_input.text()
            password = self.password_input.text()
            admin = await Admin.filter(username=username, password=password).first()
            if admin:
                self.main_window.isAdmin = True
                self.status_label.setText(f"Вітаємо, {username}!")
                await asyncio.sleep(1)
                self.main_window.open_projects_list()
            else:
                self.status_label.setText("Невірний логін або пароль")
        AsyncioPySide6.runTask(run_login())

    def guest_login(self):
        self.main_window.isAdmin = False
        self.status_label.setText("Вхід як гість успішний")
        self.main_window.open_projects_list()
