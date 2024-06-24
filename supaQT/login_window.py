from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox)
from PyQt5.QtCore import pyqtSignal

class LoginWindow(QDialog):
    login_successful = pyqtSignal(str)

    def __init__(self, login_manager):
        super().__init__()
        self.login_manager = login_manager
        self.setWindowTitle("Login")
        self.setGeometry(300, 300, 300, 150)

        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        layout.addWidget(QLabel("Username:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)

        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.register_button = QPushButton("Register")
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.login_button.clicked.connect(self.login)
        self.register_button.clicked.connect(self.register)

        self.login_manager.login_success.connect(self.on_login_success)
        self.login_manager.login_failed.connect(self.on_login_failed)
        self.login_manager.registration_success.connect(self.on_registration_success)
        self.login_manager.registration_failed.connect(self.on_registration_failed)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        self.login_manager.login(username, password)

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        self.login_manager.register(username, password)

    def on_login_success(self, message):
        self.login_successful.emit(message)
        self.accept()

    def on_login_failed(self, error):
        QMessageBox.critical(self, "Login Failed", error)

    def on_registration_success(self, message):
        QMessageBox.information(self, "Registration Successful", message)

    def on_registration_failed(self, error):
        QMessageBox.critical(self, "Registration Failed", error)
