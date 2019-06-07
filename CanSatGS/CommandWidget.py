from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class CommandWidget(QWidget):

    command_sent = pyqtSignal(str)

    def __init__(self, commands):
        super().__init__()

        assert type(commands) == dict, "Command list must be dict"

        self.commands = commands

        self.init_ui(commands)

    def init_ui(self, commands):
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        layout = QGridLayout()
        self.setLayout(layout)
        # layout.setContentsMargins(0, 0, 0, 0)

        i = 0
        for text, cmd in commands.items():
            button = QPushButton(text)
            button.clicked.connect(lambda checked, arg=cmd+"\n": self.send_command(arg))
            layout.addWidget(button, int(i/2), int(i%2))
            i += 1

    def send_command(self, command):
        self.command_sent.emit(command)