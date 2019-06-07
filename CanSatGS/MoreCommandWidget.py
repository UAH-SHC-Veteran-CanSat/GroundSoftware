from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class MoreCommandWidget(QWidget):
    command_sent = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        layout = QGridLayout()
        self.setLayout(layout)

        pid_button = QPushButton("Update PID")
        state_button = QPushButton("Set State")
        custom_button = QPushButton("Custom Command")

        kp_box = QLineEdit()
        kp_box.setPlaceholderText("Kp")
        kp_box.setValidator(QDoubleValidator())
        ki_box = QLineEdit()
        ki_box.setPlaceholderText("Ki")
        ki_box.setValidator(QDoubleValidator())
        kd_box = QLineEdit()
        kd_box.setPlaceholderText("Kd")
        kd_box.setValidator(QDoubleValidator())

        pid_button.clicked.connect(lambda clicked:
                                   self.send_command("PID," + kp_box.text() + "," + ki_box.text() + "," + kd_box.text() + "\n"))

        state_box = QLineEdit()
        state_box.setPlaceholderText("State #")
        state_box.setValidator(QIntValidator())

        state_button.clicked.connect(lambda clicked:
                                     self.send_command("STATE," + state_box.text() + "\n"))

        custom_box = QLineEdit()
        custom_box.setPlaceholderText("Command")

        custom_button.clicked.connect(lambda clicked:
                                     self.send_command(custom_box.text() + "\n"))

        layout.addWidget(pid_button, 0, 0)
        layout.addWidget(kp_box, 0, 1)
        layout.addWidget(ki_box, 0, 2)
        layout.addWidget(kd_box, 0, 3)

        layout.addWidget(state_button, 1, 0)
        layout.addWidget(state_box, 1, 1, 1, 3)

        layout.addWidget(custom_button, 2, 0)
        layout.addWidget(custom_box, 2, 1, 1, 3)


    def send_command(self, command):
        print(command)
        self.command_sent.emit(command)
