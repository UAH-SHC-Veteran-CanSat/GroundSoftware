from PyQt5.QtCore import *

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

class CommsParser(QObject):

    parsed = pyqtSignal(dict)
    packet = pyqtSignal(str)
    command = pyqtSignal(str)
    message = pyqtSignal(str)
    error = pyqtSignal(str)
    warning = pyqtSignal(str)
    csv_headers = pyqtSignal(str)

    def __init__(self, names, exponents):
        super().__init__()
        self.names = names
        self.exponents = exponents
        assert (len(names) == len(exponents)), "Names and Exponents not same length"

        self.first_parse = True

    def parse(self, text):

        if self.first_parse:
            self.first_parse = False
            self.csv_headers.emit(",".join(self.names))

        if text.startswith("CMD TX:"):
            self.command.emit(text)
            return

        if "unexpected" in text or "Too many retries" in text or "failed" in text:
            self.error.emit(text)
            return

        comma_count = text.count(",")
        if comma_count > 0 and comma_count != len(self.names)-1:
            print("Attempted to parse malformed packet")
            self.warning.emit(text)
            return
        elif comma_count <= 0:
            if is_number(text):
                self.warning.emit(text)
            else:
                self.message.emit(text)
            return

        value_array = text.split(",")

        output_dict = {}

        for i in range(0, len(self.names)):
            try:
                if type(self.exponents[i]) is int:
                    output_dict[self.names[i]] = float(value_array[i]) * 10.0**float(self.exponents[i])
                else:
                    output_dict[self.names[i]] = value_array[i]
            except:
                print("Parse failure\n")

        self.parsed.emit(output_dict)
        self.packet.emit(text)
