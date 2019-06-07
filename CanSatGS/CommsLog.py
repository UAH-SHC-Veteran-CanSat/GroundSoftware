import os

from PyQt5.QtWidgets import *


def file_is_empty(path):
    return os.stat(path).st_size==0

class CommsLog(QWidget):

    def __init__(self):
        super().__init__()

        self.logging_enabled = False

        self.raw_file = "defaultRaw.txt"
        self.csv_file = "defaultCSV.csv"

        self.csv_headers = "No headers :("

        self.init_ui()


    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.setMinimumWidth(750)
        layout = QGridLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        self.textbox = QPlainTextEdit()
        self.textbox.setReadOnly(True)
        self.textbox.setMaximumBlockCount(250)
        self.textbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.raw_btn = QPushButton("Set Log File")
        self.raw_btn.clicked.connect(self.show_raw_file_dialog)

        self.csv_btn = QPushButton("Set CSV File")
        self.csv_btn.clicked.connect(self.show_csv_file_dialog)

        self.enable_btn = QPushButton("Enable File Output")
        self.enable_btn.clicked.connect(self.set_logging)

        self.raw_box = QLineEdit(self.raw_file)
        self.raw_box.setReadOnly(True)
        self.raw_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        self.csv_box = QLineEdit(self.csv_file)
        self.csv_box.setReadOnly(True)
        self.csv_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        layout.addWidget(self.textbox, 0, 0, 5, 1)
        layout.addWidget(self.raw_btn, 1, 1)
        layout.addWidget(self.csv_btn, 3, 1)
        layout.addWidget(self.enable_btn, 0, 1)
        layout.addWidget(self.raw_box, 2, 1)
        layout.addWidget(self.csv_box, 4, 1)

    def show_raw_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "", "Text Files (*.txt)", options=options)
        if file_name:
            if not file_name.endswith(".txt"):
                file_name = file_name.split(".")[0]+".txt"
            self.raw_file = file_name
            self.raw_box.setText(self.raw_file)

    def show_csv_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "", "Comma Separated Variable Files (*.csv)",
                                                   options=options)
        if file_name:
            if not file_name.endswith(".csv"):
                file_name = file_name.split(".")[0] + ".csv"
            self.csv_file = file_name
            self.csv_box.setText(self.csv_file)

    def set_logging(self):
        self.logging_enabled = not self.logging_enabled
        self.raw_btn.setEnabled(not self.logging_enabled)
        self.csv_btn.setEnabled(not self.logging_enabled)
        self.raw_box.setEnabled(not self.logging_enabled)
        self.csv_box.setEnabled(not self.logging_enabled)
        if self.logging_enabled:
            self.enable_btn.setText("Disable File Output")
        else:
            self.enable_btn.setText("Enable File Output")

    def log_text(self, text, color):
        self.textbox.appendHtml("<font color="+color+">"+text+"</font>")
        if self.logging_enabled and self.raw_file:
            with open(self.raw_file, "a") as text_file:
                text_file.write(text+"\n")

    def log_packet(self, text):
        self.log_text(text, "white")
        if self.logging_enabled and self.csv_file:
            with open(self.csv_file, "a") as text_file:
                if file_is_empty(self.csv_file):
                    text_file.write(self.csv_headers+"\n")
                text_file.write(text+"\n")

    def log_command(self, text):
        self.log_text(text, "dodgerblue")

    def log_message(self, text):
        self.log_text(text, "limegreen")

    def log_error(self, text):
        self.log_text(text, "red")

    def log_warning(self, text):
        self.log_text(text, "yellow")

    def set_headers(self, text):
        self.csv_headers = text
