from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class StateDisplay(QWidget):

    def __init__(self, state_key, met_key, utc_key, packet_key):
        super().__init__()

        self.state_key = state_key
        self.met_key = met_key
        self.utc_key = utc_key
        self.packet_key = packet_key

        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.state_box = QLineEdit()
        self.state_box.setReadOnly(True)
        f = QFont()
        f.setBold(True)
        f.setPointSize(24)
        self.state_box.setFont(f)
        self.state_box.setAlignment(Qt.AlignCenter)
        self.state_box.setMinimumSize(160, 0)

        self.packet_box = QLineEdit()
        self.packet_box.setReadOnly(True)
        self.packet_box.setAlignment(Qt.AlignCenter)

        self.utc_box = QLCDNumber()
        self.utc_box.setDigitCount(8)
        self.utc_box.display("00:00:00")
        self.met_box = QLCDNumber()
        self.met_box.setDigitCount(8)
        self.met_box.display("00:00:00")

        layout.addWidget(QLabel("State:"), 0, 0)
        layout.addWidget(QLabel("Packets:"), 3, 0)
        layout.addWidget(QLabel("MET:"), 1, 0)
        layout.addWidget(QLabel("UTC:"), 2, 0)

        layout.addWidget(self.state_box, 0, 1)
        layout.addWidget(self.packet_box, 3, 1)
        layout.addWidget(self.met_box, 1, 1)
        layout.addWidget(self.utc_box, 2, 1)

    def update_state(self, dictionary):
        self.state_box.setText(dictionary[self.state_key])

        self.packet_box.setText(str(int(dictionary[self.packet_key])))

        utc_time = int(dictionary[self.utc_key])
        utc_seconds = str(int(utc_time % 60)).zfill(2)
        utc_minutes = str(int((int(utc_time/60)) % 60)).zfill(2)
        utc_hours = str(int((utc_time/60)/60)).zfill(2)
        utc_text = utc_hours+":"+utc_minutes+":"+utc_seconds
        self.utc_box.display(utc_text)

        met_time = dictionary[self.met_key]
        met_seconds = str(int(met_time % 60)).zfill(2)
        met_minutes = str(int((int(met_time/60)) % 60)).zfill(2)
        met_hours = str(int((met_time/60)/60)).zfill(2)
        self.met_box.display(met_hours+":"+met_minutes+":"+met_seconds)