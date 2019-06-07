import queue
import time

import serial
import serial.tools.list_ports
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


def list_ports():
    return serial.tools.list_ports.comports()


class SerialConnectionWidget(QWidget):

    opened = pyqtSignal()
    closed = pyqtSignal()
    received = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.threadpool = QThreadPool()
        self.port = ""
        self.baud = 0
        self.timeout = 1
        self.comm_thread = None

        self.init_ui()

    def init_ui(self):

        layout = QGridLayout(self)
        # layout.setContentsMargins(0, 0, 0, 0)

        port_label = QLabel("Port")
        port_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.port_list = QComboBox()
        self.port_list.currentTextChanged.connect(self.set_port)
        self.refresh_ports()

        self.refresh_btn = QPushButton("Refresh Ports")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.refresh_btn.setFixedWidth(100)

        baud_label = QLabel("Baud")
        baud_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.baud_list = QComboBox()
        self.baud_list.addItems(["110", "300", "600", "1200", "2400", "4800", "9600", "14400", "19200", "38400", "57600",
                              "115200", "128000", "256000"])
        self.baud_list.currentTextChanged.connect(self.set_baud)
        self.baud_list.setCurrentIndex(11)

        timeout_label = QLabel("Timeout")
        timeout_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.timeout_box = QLineEdit()
        self.timeout_box.setText("1")
        self.timeout_box.textChanged.connect(self.set_timeout)

        subwidget = QWidget()
        sublayout = QHBoxLayout(subwidget)
        sublayout.setContentsMargins(0, 0, 0, 0)

        self.open_button = QPushButton("Open Port")
        self.open_button.clicked.connect(self.open_port)

        self.close_button = QPushButton("Close Port")
        self.close_button.clicked.connect(self.close_port)
        self.close_button.clicked.connect(self.refresh_ports)
        self.close_button.setEnabled(False)

        sublayout.addWidget(self.open_button)
        sublayout.addWidget(self.close_button)

        layout.addWidget(port_label, 0, 0)
        layout.addWidget(self.port_list, 0, 1)
        layout.addWidget(self.refresh_btn, 0, 2)
        layout.addWidget(baud_label, 1, 0)
        layout.addWidget(self.baud_list, 1, 1, 1, 2)
        layout.addWidget(timeout_label, 2, 0)
        layout.addWidget(self.timeout_box, 2, 1, 1, 2)
        layout.addWidget(subwidget, 3, 0, 1, 3)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def refresh_ports(self):
        self.port_list.clear()
        self.port_list.addItems([row[0] for row in list_ports()])
        self.port_list.setCurrentIndex(self.port_list.count()-1)

    def set_port(self, port):
        try:
            self.port = str(port)
        except:
            self.port = ""
        print("Port changed to "+self.port)

    def set_baud(self, baud):
        try:
            self.baud = int(baud)
        except:
            self.baud = 9600
        print("Baud changed to " + str(self.baud))

    def set_timeout(self, timeout):
        try:
            self.timeout = float(timeout)
        except:
            self.timeout = 1
        print("Timeout changed to " + str(self.timeout))

    def set_edit_state(self, editable):
        self.refresh_btn.setEnabled(editable)
        self.port_list.setEnabled(editable)
        self.baud_list.setEnabled(editable)
        self.timeout_box.setEnabled(editable)
        self.open_button.setEnabled(editable)
        self.close_button.setEnabled(not editable)


    def open_port(self):
        print("Opening Port")
        self.comm_thread = SerialCommThread(self.port, self.baud, timeout=self.timeout)
        self.comm_thread.signals.receive.connect(self.on_receive)
        self.threadpool.start(self.comm_thread)

        self.opened.emit()
        self.set_edit_state(False)

    def close_port(self):
        print("Closing Port")
        self.comm_thread.signals.receive.disconnect(self.on_receive)
        self.comm_thread.close_port()

        self.closed.emit()
        self.set_edit_state(True)

    def on_receive(self, text):
        self.received.emit(text.strip())

    def transmit(self, text):
        text = str(text)
        if self.comm_thread is not None:
            self.comm_thread.transmit(text.encode("utf-8"))
            self.received.emit("CMD TX: "+text.strip())


class SerialThreadSignals(QObject):
    receive = pyqtSignal(str)


class SerialCommThread(QRunnable):

    def __init__(self, port, baud, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                 timeout=1):
        super().__init__()

        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = baud
        self.ser.parity = parity
        self.ser.stopbits = stopbits
        self.ser.bytesize = bytesize
        self.ser.timeout = timeout

        self.signals = SerialThreadSignals()

        self.tx_queue = queue.Queue()

        self.close_flag = False

    @pyqtSlot()
    def run(self):
        max_tries = 10
        num_tries = max_tries
        while not self.close_flag and num_tries > 0:
            try:
                self.ser.open()
                if num_tries < max_tries:
                    self.signals.receive.emit("Reconnected")
                else:
                    self.signals.receive.emit("Connected")
                num_tries = max_tries
                while self.ser.is_open:

                    while self.ser.in_waiting > 0:
                        self.signals.receive.emit(self.ser.readline().decode("utf-8"))

                    if not self.tx_queue.empty():
                        self.ser.write(self.tx_queue.get())

                    if self.close_flag:
                        self.ser.close()
            except:
                if num_tries < max_tries:
                    self.signals.receive.emit("Retry failed")
                else:
                    self.signals.receive.emit("Port closed unexpectedly")
                print("Port Closed Unexpectedly")
                try:
                    self.ser.close()
                except:
                    pass
            num_tries -= 1
            time.sleep(0.5)
        self.signals.receive.emit("Too many retries (Close and reopen port to reset)")


    def transmit(self, data):
        self.tx_queue.put(data)

    def close_port(self):
        self.close_flag = True
