from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTextEdit, QGroupBox,
    QGridLayout
)
import pyqtgraph as pg
from PyQt6.QtCore import QTimer
import random


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("CubeSat Ground Station")
        self.resize(1000, 700)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Connection panel
        main_layout.addWidget(self._create_connection_panel())

        # Middle layout (telemetry + plots)
        middle_layout = QHBoxLayout()
        main_layout.addLayout(middle_layout)

        middle_layout.addWidget(self._create_telemetry_panel())
        middle_layout.addWidget(self._create_plot_panel())

        # Command panel
        main_layout.addWidget(self._create_command_panel())

        # Log console
        main_layout.addWidget(self._create_log_console())

        # Fake telemetry generator (for now)
        self.timer = QTimer()
        self.timer.timeout.connect(self._generate_fake_data)
        self.timer.start(1000)

        self.time_data = []
        self.voltage_data = []
        self.t = 0

    # -------------------------
    # Connection Panel
    # -------------------------

    def _create_connection_panel(self):

        box = QGroupBox("Connection")

        layout = QHBoxLayout()

        self.com_selector = QComboBox()
        self.com_selector.addItems(["COM1", "COM2", "COM3"])

        self.baud_selector = QComboBox()
        self.baud_selector.addItems(["9600", "57600", "115200"])

        self.connect_button = QPushButton("Connect")

        layout.addWidget(QLabel("Port:"))
        layout.addWidget(self.com_selector)

        layout.addWidget(QLabel("Baud:"))
        layout.addWidget(self.baud_selector)

        layout.addWidget(self.connect_button)

        box.setLayout(layout)

        return box

    # -------------------------
    # Telemetry Panel
    # -------------------------

    def _create_telemetry_panel(self):

        box = QGroupBox("Telemetry")

        layout = QGridLayout()

        self.voltage_label = QLabel("0.0 V")
        self.temp_label = QLabel("0.0 C")
        self.mode_label = QLabel("UNKNOWN")
        self.uptime_label = QLabel("0 s")

        layout.addWidget(QLabel("Battery Voltage:"), 0, 0)
        layout.addWidget(self.voltage_label, 0, 1)

        layout.addWidget(QLabel("Temperature:"), 1, 0)
        layout.addWidget(self.temp_label, 1, 1)

        layout.addWidget(QLabel("Mode:"), 2, 0)
        layout.addWidget(self.mode_label, 2, 1)

        layout.addWidget(QLabel("Uptime:"), 3, 0)
        layout.addWidget(self.uptime_label, 3, 1)

        box.setLayout(layout)

        return box

    # -------------------------
    # Plot Panel
    # -------------------------

    def _create_plot_panel(self):

        box = QGroupBox("Voltage Plot")

        layout = QVBoxLayout()

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", "Voltage", "V")
        self.plot_widget.setLabel("bottom", "Time", "s")

        self.plot_curve = self.plot_widget.plot(pen='y')

        layout.addWidget(self.plot_widget)

        box.setLayout(layout)

        return box

    # -------------------------
    # Command Panel
    # -------------------------

    def _create_command_panel(self):

        box = QGroupBox("Commands")

        layout = QHBoxLayout()

        self.ping_button = QPushButton("Ping")
        self.reset_button = QPushButton("Reset")
        self.beacon_button = QPushButton("Start Beacon")

        layout.addWidget(self.ping_button)
        layout.addWidget(self.reset_button)
        layout.addWidget(self.beacon_button)

        box.setLayout(layout)

        return box

    # -------------------------
    # Log Console
    # -------------------------

    def _create_log_console(self):

        box = QGroupBox("Console")

        layout = QVBoxLayout()

        self.console = QTextEdit()
        self.console.setReadOnly(True)

        layout.addWidget(self.console)

        box.setLayout(layout)

        return box

    # -------------------------
    # Fake Telemetry
    # -------------------------

    def _generate_fake_data(self):

        voltage = 7 + random.random()
        temp = 25 + random.random() * 5

        self.voltage_label.setText(f"{voltage:.2f} V")
        self.temp_label.setText(f"{temp:.2f} C")
        self.mode_label.setText("NOMINAL")

        self.t += 1
        self.uptime_label.setText(str(self.t))

        self.time_data.append(self.t)
        self.voltage_data.append(voltage)

        self.plot_curve.setData(self.time_data, self.voltage_data)

        self.console.append(f"Telemetry received: V={voltage:.2f} T={temp:.2f}")
