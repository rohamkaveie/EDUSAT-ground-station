from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from datetime import datetime


class PacketMonitorWidget(QWidget):
    def __init__(self, max_rows=500, parent=None):
        super().__init__(parent)
        self.max_rows = max_rows

        self.layout = QVBoxLayout(self)

        # Header row
        header_layout = QHBoxLayout()
        title = QLabel("Packet Monitor")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_button)

        self.layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget(0, 4)
        self.table.setObjectName("packet_table")
        self.table.setHorizontalHeaderLabels(["Time", "Length", "HEX", "ASCII"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Length
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # HEX
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # ASCII

        self.layout.addWidget(self.table)

    def clear(self):
        self.table.setRowCount(0)

    def add_packet(self, data: bytes):
        if not data:
            return

        print(data)

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        hex_str = " ".join(f"{b:02X}" for b in data)
        ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in data)

        row = self.table.rowCount()
        self.table.insertRow(row)

        time_item = QTableWidgetItem(timestamp)
        length_item = QTableWidgetItem(str(len(data)))
        hex_item = QTableWidgetItem(hex_str)
        ascii_item = QTableWidgetItem(ascii_str)

        # Optional alignment
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        length_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Optional monospace-like styling cue
        hex_item.setForeground(QColor("#00AA00"))
        ascii_item.setForeground(QColor("#CCCCCC"))

        self.table.setItem(row, 0, time_item)
        self.table.setItem(row, 1, length_item)
        self.table.setItem(row, 2, hex_item)
        self.table.setItem(row, 3, ascii_item)

        # Enforce max rows
        if self.table.rowCount() > self.max_rows:
            self.table.removeRow(0)

        # Auto-scroll to bottom
        self.table.scrollToBottom()
