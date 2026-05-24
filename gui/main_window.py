import sys
import random
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTextEdit,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QListWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QTimer
import pyqtgraph as pg

import re

from communication.serial_interface import SerialInterface
from communication.receiver_thread import ReceiverThread
from gui.packet_monitor import PacketMonitorWidget
from protocol.command_packet import build_command_packet
from protocol.telemetry_processor import TelemetryProcessor
from protocol.tlm_decoder import TelemetryDecoder



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CubeSat Ground Station")
        self.resize(1200, 800)

        self.serial_interface = SerialInterface()
        self.tlm_processor = TelemetryProcessor() 
        self.decoder = TelemetryDecoder()
        self.receiver_thread = None

        self._build_ui()
        self.refresh_ports()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # ---------------- Connection Panel ----------------
        connection_group = QGroupBox("Connection")
        connection_layout = QHBoxLayout()

        self.port_combo = QComboBox()
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("115200")

        self.refresh_button = QPushButton("Refresh")
        self.connect_button = QPushButton("Connect")

        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.toggle_connection)

        connection_layout.addWidget(QLabel("Port:"))
        connection_layout.addWidget(self.port_combo)
        connection_layout.addWidget(QLabel("Baud:"))
        connection_layout.addWidget(self.baud_combo)
        connection_layout.addWidget(self.refresh_button)
        connection_layout.addWidget(self.connect_button)

        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)

        # ---------------- Top Section ----------------

        # Main Tab Container
        self.tabs = QTabWidget()

        # 1. Telemetry Tab
        telemetry_tab = QWidget()
        tlm_layout = QGridLayout()
        self.voltage_label = QLabel("0.0 V")

        # ... inside Telemetry Tab setup ...
        self.tlm_table = QTableWidget(0, 3)
        self.tlm_table.setHorizontalHeaderLabels(["Variable", "Timestamp", "Value"])
        self.tlm_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tlm_layout.addWidget(self.tlm_table)

        # ... (add your labels to tlm_layout) ...
        telemetry_tab.setLayout(tlm_layout)



        # 2. Events Tab
        events_tab = QWidget()
        # (add a QListWidget or QTextEdit here for event logs)

        # In _build_ui, inside Events Tab setup
        self.event_list = QListWidget()
        events_layout = QGridLayout()
        events_layout.addWidget(self.event_list)

        # In process_telemetry (when category == 'event')
        # self.event_list.addItem(f"{datetime.now().strftime('%H:%M:%S')} - {data['msg']} (Val: {data['val']})")
        # Scroll to bottom automatically
        self.event_list.scrollToBottom()


        # 3. Camera Tab
        camera_tab = QWidget()
        # (add a placeholder for image display)

        # 4. Graph Tab
        graph_tab = QWidget()
        graph_layout = QVBoxLayout()
        self.plot_widget = pg.PlotWidget()
        graph_layout.addWidget(self.plot_widget)
        graph_tab.setLayout(graph_layout)

        # Add tabs to the widget
        self.tabs.addTab(telemetry_tab, "Telemetry")
        self.tabs.addTab(events_tab, "Events")
        self.tabs.addTab(camera_tab, "Camera")
        self.tabs.addTab(graph_tab, "Graph")

        # Add tab widget to main layout
        main_layout.addWidget(self.tabs)

        # ---------------- Command Panel ----------------
        command_group = QGroupBox("Commands")
        command_layout = QHBoxLayout()

        command_layout = QHBoxLayout()

        cmd_label = QLabel("CmdID (HEX):")

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("e.g. 0A")

        self.send_cmd_button = QPushButton("Send")
        self.send_cmd_button.clicked.connect(self.send_command)

        command_layout.addWidget(cmd_label)
        command_layout.addWidget(self.cmd_input)
        command_layout.addWidget(self.send_cmd_button)

        main_layout.addLayout(command_layout)

        # ---------------- Packet Monitor ----------------
        self.packet_monitor = PacketMonitorWidget(max_rows=500)
        main_layout.addWidget(self.packet_monitor, 2)

        # ---------------- Log Console ----------------
        console_group = QGroupBox("Console")
        console_layout = QVBoxLayout()

        self.console = QTextEdit()
        self.console.setReadOnly(True)

        console_layout.addWidget(self.console)
        console_group.setLayout(console_layout)
        main_layout.addWidget(console_group, 1)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = self.serial_interface.list_ports()
        self.port_combo.addItems(ports)
        self.log(f"Found ports: {ports if ports else 'None'}")

    def toggle_connection(self):
        if self.serial_interface.is_connected():
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port = self.port_combo.currentText()
        baud = int(self.baud_combo.currentText())

        if not port:
            self.log("No COM port selected.")
            return

        try:
            self.serial_interface.connect(port, baud)
            self.receiver_thread = ReceiverThread(self.serial_interface, self.tlm_processor)
            self.receiver_thread.raw_received.connect(self.handle_received_data)
            self.receiver_thread.packet_received.connect(self.handle_telemetry_packets)

            self.receiver_thread.status_message.connect(self.log)
            self.receiver_thread.error_occurred.connect(self.log)
            self.receiver_thread.start()

            self.connect_button.setText("Disconnect")
            self.log(f"Connected to {port} @ {baud}")
        except Exception as e:
            self.log(f"Connection error: {e}")

    def disconnect_serial(self):
        try:
            if self.receiver_thread is not None:
                self.receiver_thread.stop()
                self.receiver_thread.wait()
                self.receiver_thread = None

            self.serial_interface.disconnect()
            self.connect_button.setText("Connect")
            self.log("Disconnected.")
        except Exception as e:
            self.log(f"Disconnection error: {e}")

    def handle_received_data(self, data: bytes):
        if not data:
            return

        # Add to packet monitor
        self.packet_monitor.add_packet(data)

        # Keep existing console logging too
        hex_str = " ".join(f"{b:02X}" for b in data)
        ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in data)

        self.log(f"RX [{len(data)} bytes]")
        self.log(f"HEX: {hex_str}")
        self.log(f"ASCII: {ascii_str}")

    def send_command(self):
        if not self.serial_interface.is_connected():
            self.log("Cannot send: not connected.")
            return

        hex_text = self.cmd_input.text().strip()

        try:

            clean_hex = re.sub(r'[^0-9A-Fa-f]', '', hex_text)

            if len(clean_hex) % 2 != 0:
                raise ValueError("Hex string must contain full bytes")

            cmd_opcode = bytes.fromhex(clean_hex)

            packet = build_command_packet(cmd_opcode)
            self.serial_interface.write(packet)
            self.log(f"Sent Packet: {packet}")
        except Exception as e:
            self.log(f"Send error: {e}")

    def log(self, message: str):
        self.console.append(message)

    def closeEvent(self, event):
        try:
            self.disconnect_serial()
        except Exception:
            pass
        event.accept()

    def update_telemetry_ui(self, data):
        """
        data = {"name": "Solar Voltage", "val": "3.75 V", "time": 12345}
        """
        name = data['name']
        
        # Check if row already exists for this variable
        items = self.tlm_table.findItems(name, Qt.MatchFlag.MatchExactly)
        
        if items:
            # Update existing row
            row = items[0].row()
            self.tlm_table.setItem(row, 1, QTableWidgetItem(str(data['time'])))
            self.tlm_table.setItem(row, 2, QTableWidgetItem(data['val']))
        else:
            # Add new row
            row = self.tlm_table.rowCount()
            self.tlm_table.insertRow(row)
            self.tlm_table.setItem(row, 0, QTableWidgetItem(name))
            self.tlm_table.setItem(row, 1, QTableWidgetItem(str(data['time'])))
            self.tlm_table.setItem(row, 2, QTableWidgetItem(data['val']))

    def handle_telemetry_packets(self, pkt):
        category, data = self.decoder.decode(pkt['tlm_id'], pkt['payload'],pkt['timestamp'])
        
        if category == "telemetry":
            # Update Telemetry Tab
            self.update_telemetry_ui(data) 
            # Update Graph Tab
            # self.update_graph(data['name'], float(data['val'].split()[0]))
            
        elif category == "event":
            # Update Event Tab
            self.event_list.addItem(f"[{data['time']}] {data['msg']} (Code: {data['val']})")
