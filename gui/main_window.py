from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTextEdit, QGroupBox,
    QGridLayout, QMessageBox
)
from PyQt6.QtCore import QTimer
import pyqtgraph as pg
import random

from communication.serial_interface import SerialInterface
from communication.receiver_thread import ReceiverThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CubeSat Ground Station")
        self.resize(1100, 750)

        self.serial_interface = SerialInterface()
        self.receiver_thread = None
        self.connected = False

        self.time_data = []
        self.voltage_data = []
        self.t = 0

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        main_layout.addWidget(self._create_connection_panel())

        middle_layout = QHBoxLayout()
        main_layout.addLayout(middle_layout)
        middle_layout.addWidget(self._create_telemetry_panel(), 1)
        middle_layout.addWidget(self._create_plot_panel(), 2)

        main_layout.addWidget(self._create_command_panel())
        main_layout.addWidget(self._create_log_console(), 1)

        self._connect_signals()
        self.refresh_ports()

        # Temporary fake telemetry until CCSDS decoding is added
        self.timer = QTimer()
        self.timer.timeout.connect(self._generate_fake_data)
        self.timer.start(1000)

    # -------------------------
    # UI Creation
    # -------------------------

    def _create_connection_panel(self):
        box = QGroupBox("Connection")
        layout = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh Ports")
        self.com_selector = QComboBox()

        self.baud_selector = QComboBox()
        self.baud_selector.addItems(["9600", "19200", "57600", "115200"])
        self.baud_selector.setCurrentText("115200")

        self.connect_button = QPushButton("Connect")

        layout.addWidget(QLabel("Port:"))
        layout.addWidget(self.com_selector)

        layout.addWidget(QLabel("Baud:"))
        layout.addWidget(self.baud_selector)

        layout.addWidget(self.refresh_button)
        layout.addWidget(self.connect_button)

        box.setLayout(layout)
        return box

    def _create_telemetry_panel(self):
        box = QGroupBox("Telemetry")
        layout = QGridLayout()

        self.voltage_label = QLabel("0.00 V")
        self.temp_label = QLabel("0.00 C")
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

    def _create_plot_panel(self):
        box = QGroupBox("Voltage Plot")
        layout = QVBoxLayout()

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", "Voltage", "V")
        self.plot_widget.setLabel("bottom", "Time", "s")
        self.plot_widget.showGrid(x=True, y=True)

        self.plot_curve = self.plot_widget.plot(pen="y")

        layout.addWidget(self.plot_widget)
        box.setLayout(layout)
        return box

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

    def _create_log_console(self):
        box = QGroupBox("Console")
        layout = QVBoxLayout()

        self.console = QTextEdit()
        self.console.setReadOnly(True)

        layout.addWidget(self.console)
        box.setLayout(layout)
        return box

    # -------------------------
    # Signals
    # -------------------------

    def _connect_signals(self):
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.toggle_connection)

        self.ping_button.clicked.connect(lambda: self.send_raw_command(b"PING\n"))
        self.reset_button.clicked.connect(lambda: self.send_raw_command(b"RESET\n"))
        self.beacon_button.clicked.connect(lambda: self.send_raw_command(b"BEACON_ON\n"))

    # -------------------------
    # Serial Management
    # -------------------------

    def refresh_ports(self):
        current = self.com_selector.currentText()
        ports = self.serial_interface.list_ports()

        self.com_selector.clear()
        self.com_selector.addItems(ports)

        if current in ports:
            self.com_selector.setCurrentText(current)

        self.log(f"Available ports: {ports if ports else 'No ports found'}")

    def toggle_connection(self):
        if not self.connected:
            self.connect_serial()
        else:
            self.disconnect_serial()

    def connect_serial(self):
        port = self.com_selector.currentText().strip()
        baud_text = self.baud_selector.currentText().strip()

        if not port:
            QMessageBox.warning(self, "Connection Error", "Please select a COM port.")
            return

        try:
            baudrate = int(baud_text)
            self.serial_interface.connect(port, baudrate)

            self.receiver_thread = ReceiverThread(self.serial_interface)
            self.receiver_thread.data_received.connect(self.on_raw_data_received)
            self.receiver_thread.error_occurred.connect(self.on_receiver_error)
            self.receiver_thread.status_changed.connect(self.log)
            self.receiver_thread.start()

            self.connected = True
            self.connect_button.setText("Disconnect")
            self.log(f"Connected to {port} @ {baudrate} baud.")

        except Exception as e:
            QMessageBox.critical(self, "Connection Failed", str(e))
            self.log(f"Connection failed: {e}")

    def disconnect_serial(self):
        try:
            if self.receiver_thread is not None:
                self.receiver_thread.stop()
                self.receiver_thread.wait()
                self.receiver_thread = None

            self.serial_interface.disconnect()
            self.connected = False
            self.connect_button.setText("Connect")
            self.log("Serial disconnected.")

        except Exception as e:
            self.log(f"Disconnection error: {e}")

    # -------------------------
    # Thread Callbacks
    # -------------------------

    def on_raw_data_received(self, data: bytes):
        hex_str = data.hex(" ").upper()
        ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in data)

        self.log(f"RX {len(data)} bytes")
        self.log(f"HEX: {hex_str}")
        self.log(f"ASCII: {ascii_str}")

    def on_receiver_error(self, message: str):
        self.log(f"Receiver error: {message}")
        self.disconnect_serial()

    # -------------------------
    # Send Commands
    # -------------------------

    def send_raw_command(self, data: bytes):
        if not self.connected:
            self.log("Cannot send command: not connected.")
            return

        try:
            self.serial_interface.write(data)
            self.log(f"TX {len(data)} bytes: {data!r}")
        except Exception as e:
            self.log(f"Send error: {e}")

    # -------------------------
    # Logging
    # -------------------------

    def log(self, message: str):
        self.console.append(message)

    # -------------------------
    # Temporary Fake Telemetry
    # -------------------------

    def _generate_fake_data(self):
        voltage = 7.0 + random.random()
        temp = 25.0 + random.random() * 5.0

        self.voltage_label.setText(f"{voltage:.2f} V")
        self.temp_label.setText(f"{temp:.2f} C")
        self.mode_label.setText("NOMINAL")

        self.t += 1
        self.uptime_label.setText(f"{self.t} s")

        self.time_data.append(self.t)
        self.voltage_data.append(voltage)

        if len(self.time_data) > 100:
            self.time_data = self.time_data[-100:]
            self.voltage_data = self.voltage_data[-100:]

        self.plot_curve.setData(self.time_data, self.voltage_data)

    # -------------------------
    # Cleanup
    # -------------------------

    def closeEvent(self, event):
        self.disconnect_serial()
        event.accept()
