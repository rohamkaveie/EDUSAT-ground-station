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
    QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QTimer
import pyqtgraph as pg

import re

from controllers.ground_station_controller import GroundStationController
from views.packet_monitor import PacketMonitorWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... (Your existing UI setup code / UI.load or Manual Setup) ...
        self.resize(1200, 800)

        self._build_ui()
  
        self.controller = GroundStationController()
        self.controller.packet_received.connect(self._handle_received_packet)

        self.refresh_ports()    




        self.controller.status_message.connect(self.log)
        self.controller.error_message.connect(self.log)


    def send_command(self):

        hex_text = self.cmd_input.text().strip()
        self.controller.sendCommand(hex_text)        

    def refresh_ports(self):
        self.port_combo.clear()
        ports = self.controller.getListPorts()
        self.port_combo.addItems(ports)
        self.log(f"Found ports: {ports if ports else 'None'}")

    def toggle_connection(self):
        if not self.controller.is_connected():
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            self.controller.connect_serial(port, baud)
            self.connect_button.setText("Disconnect")
        else:
            self.controller.disconnect_serial()
            self.connect_button.setText("Connect")

    def log(self, message: str):
        self.console.append(message)

    def _log_server_command(self, cmd: dict):
        self.log(f"--- Incoming Server Command: ID {cmd.get('cmd_id')} ---")

    def _handle_received_packet(self, packet :dict):
        self.packet_monitor.add_packet(packet['raw'])
        self._add_packet_to_telemetry_tab(packet)

    def _add_packet_to_telemetry_tab(self, packet: dict):
        row = self.tlm_table.rowCount()
        self.tlm_table.insertRow(row)

        # Example fields — adjust keys to your packet structure
        variable = packet.get("tlm_id", "packet")
        timestamp = packet.get("timestamp", "")
        value = packet.get("payload", "")

        self.tlm_table.setItem(row, 0, QTableWidgetItem(str(variable)))
        self.tlm_table.setItem(row, 1, QTableWidgetItem(str(timestamp)))
        self.tlm_table.setItem(row, 2, QTableWidgetItem(str(value)))


    def closeEvent(self, event):
        """Ensure threads close when window is closed."""
        self.controller.cleanup()
        event.accept()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        splitter = QSplitter(Qt.Orientation.Vertical)

        main_layout.addWidget(splitter)



        # ---------------- Connection Panel ----------------
        connection_group = QGroupBox("Connection")
        connection_layout = QHBoxLayout()

        self.port_combo = QComboBox()
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("115200")

        self.refresh_button = QPushButton("Refresh")
        self.connect_button = QPushButton("Connect")
        self.connect_button.setObjectName("connect_btn")

        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.toggle_connection)

        connection_layout.addWidget(QLabel("Port:"))
        connection_layout.addWidget(self.port_combo)
        connection_layout.addWidget(QLabel("Baud:"))
        connection_layout.addWidget(self.baud_combo)
        connection_layout.addWidget(self.refresh_button)
        connection_layout.addWidget(self.connect_button)

        connection_group.setLayout(connection_layout)
        # main_layout.addWidget(connection_group)
        splitter.addWidget(connection_group)

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

        pg.setConfigOptions(
            background="#FFFFFF",
            foreground="#2B3446",
            antialias=True
        )

        self.plot_widget = pg.PlotWidget()

        self.plot_widget.setBackground("#FFFFFF")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)

        # Axis styles
        axis_pen = pg.mkPen(color="#2B3446", width=1)
        for axis in ["left", "bottom"]:
            self.plot_widget.getAxis(axis).setPen(axis_pen)
            self.plot_widget.getAxis(axis).setTextPen("#2B3446")

        # Curve style
        curve_pen = pg.mkPen(color="#EDB96F", width=2)
        self.curve = self.plot_widget.plot(pen=curve_pen)

        graph_layout.addWidget(self.plot_widget)
        graph_tab.setLayout(graph_layout)

        # Add tabs to the widget
        self.tabs.addTab(telemetry_tab, "Telemetry")
        self.tabs.addTab(events_tab, "Events")
        self.tabs.addTab(camera_tab, "Camera")
        self.tabs.addTab(graph_tab, "Graph")

        # Add tab widget to main layout
        # main_layout.addWidget(self.tabs)
        splitter.addWidget(self.tabs)
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

        command_group.setLayout(command_layout)

        # main_layout.addLayout(command_layout)
        # main_layout.addWidget(command_group,1)

        splitter.addWidget(command_group)

        # ---------------- Packet Monitor ----------------
        self.packet_monitor = PacketMonitorWidget(max_rows=500)
        # main_layout.addWidget(self.packet_monitor, 2)
        splitter.addWidget(self.packet_monitor)

        # ---------------- Log Console ----------------
        console_group = QGroupBox("Console")
        console_layout = QVBoxLayout()

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("console_output")

        console_layout.addWidget(self.console)
        console_group.setLayout(console_layout)
        splitter.addWidget(console_group)
        # main_layout.addWidget(console_group, 1)



