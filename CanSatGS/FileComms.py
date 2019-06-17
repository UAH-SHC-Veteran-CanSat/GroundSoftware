import queue
import time

import serial
import serial.tools.list_ports
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *




class FileConnectionWidget(QWidget):

    opened = pyqtSignal()
    closed = pyqtSignal()
    received = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.threadpool = QThreadPool()

        self.file_name = ""

        self.init_ui()

    def init_ui(self):

        layout = QGridLayout(self)
        # layout.setContentsMargins(0, 0, 0, 0)

        self.raw_btn = QPushButton("Open Log File")
        self.raw_btn.clicked.connect(self.show_open_file_dialog)

        self.start_btn = QPushButton("Start Playback")
        self.start_btn.clicked.connect(self.open_file)

        layout.addWidget(self.raw_btn, 0, 0)
        layout.addWidget(self.start_btn, 1, 0)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


    def on_receive(self, text):
        self.received.emit(text.strip())

    def open_file(self):
        print("Opening File")
        self.comm_thread = FileCommThread(self.file_name)
        self.comm_thread.signals.receive.connect(self.on_receive)
        self.threadpool.start(self.comm_thread)

        self.opened.emit()

    def close_file(self):
        print("Closing File")
        self.comm_thread.signals.receive.disconnect(self.on_receive)
        self.comm_thread.close_port()

        self.closed.emit()
        self.set_edit_state(True)

    def show_open_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "Text Files (*.txt)",
                                                   options=options)
        if file_name:
            self.file_name = file_name


class FileThreadSignals(QObject):
    receive = pyqtSignal(str)


class FileCommThread(QRunnable):

    def __init__(self, filename):
        super().__init__()

        self.filename = filename

        self.signals = FileThreadSignals()

        self.close_flag = False

    @pyqtSlot()
    def run(self):
        max_tries = 99999
        num_tries = max_tries
        while not self.close_flag and num_tries > 0:
            try:
                if num_tries < max_tries:
                    self.signals.receive.emit("Reconnected")
                else:
                    self.signals.receive.emit("Connected")
                num_tries = max_tries
                file = open(self.filename, "r")

                lines = file.readlines()
                for line in lines:

                    self.signals.receive.emit(line)
                    time.sleep(0.25)

                file.close()
            except:
                if num_tries < max_tries:
                    self.signals.receive.emit("Retry failed")
                else:
                    self.signals.receive.emit("File closed unexpectedly")
                print("File Closed Unexpectedly")
                try:
                    file.close()
                except:
                    pass
            num_tries -= 1
            time.sleep(0.5)
        self.signals.receive.emit("Too many retries (Close and reopen file to reset)")


    def close_port(self):
        self.close_flag = True
