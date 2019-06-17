import sys

from PyQt5.QtWidgets import *

import CommandWidget
import CommsLog
import CommsParser
import GPSDisplay
import GSGraph
import ModelDisplay
import SerialComms as sc
import FileComms as fc
import StateDisplay
import dark_fusion
from MoreCommandWidget import MoreCommandWidget
from QTabWidgetResize import QTabWidgetResize


huntsville = False


class Screen(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Astrotrain Ground Station")

        self.comm_w = sc.SerialConnectionWidget()
        self.file_w = fc.FileConnectionWidget()
        self.parser = CommsParser.CommsParser(["team_id", "mission_time", "packet_count", "altitude", "pressure",
                                               "temp", "voltage", "gps_time", "gps_latitude", "gps_longitude",
                                               "gps_altitude", "gps_sats", "pitch", "roll", "blade_spin_rate",
                                               "software_state", "bonus_direction"],
                                              [0, -3, 0, -1, 0, -1, -2, 0, -5, -5, -1, 0, -1, -1, 0, "str", -1])
        self.comm_w.received.connect(self.parser.parse)
        self.file_w.received.connect(self.parser.parse)
        self.log_w = CommsLog.CommsLog()
        self.parser.csv_headers.connect(self.log_w.set_headers)
        self.cmds = CommandWidget.CommandWidget({"Arm for launch": "ARM",
                                                 "Un-Arm": "STATE/0",
                                                 "Soft Reset": "RESET",
                                                 "Hard Reset": "HARD_RESET",
                                                 "Calibrate IMU": "CAL_IMU",
                                                 "Calibrate Barometer": "CAL_ALT",
                                                 "Close Release": "CLOSE",
                                                 "Open Release": "ABORT"})

        self.more_cmds = MoreCommandWidget()
        self.even_more_cmds = CommandWidget.CommandWidget({"Start Camera": "CAMON",
                                                           "Stop Camera": "CAMOFF",
                                                           "Start PID": "PIDSTART",
                                                           "Stop PID": "PIDSTOP",
                                                           "Fast TX Rate": "RATE/100",
                                                           "Slow TX Rate": "RATE/1000",
                                                           "EMERGENCY RELEASE": "STATE/4",
                                                           "Say Hi to CanSat": "Hi CanSat, how are you?"})

        self.alt_plot = GSGraph.GSGraph("mission_time", "altitude",
                                        title="Altitude", x_units="Seconds", y_units="Meters")
        self.parser.parsed.connect(self.alt_plot.update_plot)

        self.alt_plot2 = GSGraph.GSGraph("mission_time", "altitude",
                                         title="Altitude", x_units="Seconds", y_units="Meters")
        self.parser.parsed.connect(self.alt_plot2.update_plot)

        self.pressure_plot = GSGraph.GSGraph("mission_time", "pressure",
                                        title="Pressure", x_units="Seconds", y_units="Pascals")
        self.parser.parsed.connect(self.pressure_plot.update_plot)

        self.temp_plot = GSGraph.GSGraph("mission_time", "temp",
                                        title="Temperature", x_units="Seconds", y_units="Celsius")
        self.parser.parsed.connect(self.temp_plot.update_plot)

        self.volt_plot = GSGraph.GSGraph("mission_time", "voltage",
                                        title="Power Bus Voltage", x_units="Seconds", y_units="Volts")
        self.parser.parsed.connect(self.volt_plot.update_plot)

        self.volt_plot2 = GSGraph.GSGraph("mission_time", "voltage",
                                         title="Power Bus Voltage", x_units="Seconds", y_units="Volts")
        self.parser.parsed.connect(self.volt_plot2.update_plot)

        self.rpm_plot = GSGraph.GSGraph("mission_time", "blade_spin_rate",
                                        title="Blade Spin Rate", x_units="Seconds", y_units="RPM")
        self.parser.parsed.connect(self.rpm_plot.update_plot)

        self.yaw_plot = GSGraph.GSGraph("mission_time", "bonus_direction",
                                        title="Heading", x_units="Seconds", y_units="Degrees from North")
        self.parser.parsed.connect(self.yaw_plot.update_plot)

        self.yaw_plot2 = GSGraph.GSGraph("mission_time", "bonus_direction",
                                        title="Heading", x_units="Seconds", y_units="Degrees from North")
        self.parser.parsed.connect(self.yaw_plot2.update_plot)

        self.pitch_plot = GSGraph.GSGraph("mission_time", "pitch",
                                        title="Pitch", x_units="Seconds", y_units="Degrees")
        self.parser.parsed.connect(self.pitch_plot.update_plot)

        self.roll_plot = GSGraph.GSGraph("mission_time", "roll",
                                          title="Roll", x_units="Seconds", y_units="Degrees")
        self.parser.parsed.connect(self.roll_plot.update_plot)

        self.state_disp = StateDisplay.StateDisplay("software_state", "mission_time", "gps_time", "packet_count")
        self.parser.parsed.connect(self.state_disp.update_state)

        if not huntsville:
            lat_min = 32.2345
            lat_max = 32.2545
            lon_min = -98.2120
            lon_max = -98.1883
            image_name = "CroppedMap.png"

        else:
            lat_min = 34.7145
            lat_max = 34.736
            lon_min = -86.6525
            lon_max = -86.6266
            image_name = "HuntsvilleCropped.png"

        self.gps_disp = GPSDisplay.GPSDisplay("gps_latitude", "gps_longitude", "altitude", "gps_sats",
                                              lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max,
                                              image_name=image_name, max_points=600)
        self.parser.parsed.connect(self.gps_disp.update_plot)

        self.model_disp = ModelDisplay.ModelDisplay("gps_latitude", "gps_longitude", "altitude", "blade_spin_rate",
                                                    "software_state", "roll", "pitch", "bonus_direction",
                                                    lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max,
                                                    image_name=image_name, max_points=600)
        self.parser.parsed.connect(self.model_disp.update_plot)

        self.parser.packet.connect(self.log_w.log_packet)
        self.parser.message.connect(self.log_w.log_message)
        self.parser.command.connect(self.log_w.log_command)
        self.parser.error.connect(self.log_w.log_error)
        self.parser.warning.connect(self.log_w.log_warning)

        self.cmds.command_sent.connect(self.comm_w.transmit)
        self.more_cmds.command_sent.connect(self.comm_w.transmit)
        self.even_more_cmds.command_sent.connect(self.comm_w.transmit)

        layout = QVBoxLayout()
        self.setLayout(layout)

        primary_graph_holder = QWidget()
        primary_graph_layout = QGridLayout(primary_graph_holder)
        primary_graph_layout.addWidget(self.state_disp, 0, 2)
        primary_graph_layout.addWidget(self.model_disp, 0, 1)
        primary_graph_layout.addWidget(self.gps_disp, 0, 0)

        primary_graph_layout.addWidget(self.alt_plot, 1, 0)
        primary_graph_layout.addWidget(self.volt_plot, 1, 1)
        primary_graph_layout.addWidget(self.yaw_plot, 1, 2)

        secondary_graph_holder = QWidget()
        secondary_graph_layout = QGridLayout(secondary_graph_holder)
        secondary_graph_layout.addWidget(self.alt_plot2, 0, 0)
        secondary_graph_layout.addWidget(self.pressure_plot, 0, 1)
        secondary_graph_layout.addWidget(self.temp_plot, 0, 2)
        secondary_graph_layout.addWidget(self.volt_plot2, 0, 3)
        secondary_graph_layout.addWidget(self.roll_plot, 1, 0)
        secondary_graph_layout.addWidget(self.pitch_plot, 1, 1)
        secondary_graph_layout.addWidget(self.yaw_plot2, 1, 2)
        secondary_graph_layout.addWidget(self.rpm_plot, 1, 3)

        top_tabwidget = QTabWidgetResize()
        top_tabwidget.addTab(primary_graph_holder, "Primary Display")
        top_tabwidget.addTab(secondary_graph_holder, "Secondary Display")

        clear_all_btn = QPushButton("Clear All Graphs")
        clear_all_btn.setParent(top_tabwidget)
        top_tabwidget.resized.connect(lambda event: clear_all_btn.move(event.size().width()-clear_all_btn.width(), 0))
        clear_all_btn.show()
        clear_all_btn.clicked.connect(self.gps_disp.clear_plot)
        clear_all_btn.clicked.connect(self.model_disp.clear_plot)
        clear_all_btn.clicked.connect(self.alt_plot.clear_plot)
        clear_all_btn.clicked.connect(self.volt_plot.clear_plot)
        clear_all_btn.clicked.connect(self.yaw_plot.clear_plot)
        clear_all_btn.clicked.connect(self.alt_plot2.clear_plot)
        clear_all_btn.clicked.connect(self.pressure_plot.clear_plot)
        clear_all_btn.clicked.connect(self.temp_plot.clear_plot)
        clear_all_btn.clicked.connect(self.volt_plot2.clear_plot)
        clear_all_btn.clicked.connect(self.roll_plot.clear_plot)
        clear_all_btn.clicked.connect(self.pitch_plot.clear_plot)
        clear_all_btn.clicked.connect(self.yaw_plot2.clear_plot)
        clear_all_btn.clicked.connect(self.rpm_plot.clear_plot)

        botton_tabwidget = QTabWidget()
        botton_tabwidget.setMinimumWidth(450)
        botton_tabwidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        botton_tabwidget.addTab(self.comm_w, "Connection Settings")
        botton_tabwidget.addTab(self.file_w, "File Reader")
        botton_tabwidget.addTab(self.cmds, "Commands 1")
        botton_tabwidget.addTab(self.even_more_cmds, "Commands 2")
        botton_tabwidget.addTab(self.more_cmds, "Commands 3")

        bottom_layout_holder = QWidget()
        bottom_layout = QHBoxLayout(bottom_layout_holder)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addWidget(self.log_w)
        bottom_layout.addWidget(botton_tabwidget)

        layout.addWidget(top_tabwidget)
        layout.addWidget(bottom_layout_holder)


def run():
    app = QApplication(sys.argv)
    dark_fusion.set_style(app)
    w = Screen()
    w.show()
    app.exec_()


run()
