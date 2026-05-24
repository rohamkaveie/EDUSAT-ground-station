from PyQt6.QtCore import QThread, pyqtSignal
from protocol.telemetry_processor import TelemetryProcessor

class ReceiverThread(QThread):
    packet_received = pyqtSignal(dict)  # Emits the parsed packet dict
    raw_received = pyqtSignal(bytes)    # Emits raw data for monitor
    status_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, serial_interface,tlm_processor):
        super().__init__()
        self.serial_interface = serial_interface
        self.tlm_processor = tlm_processor
        self.running = True

    def run(self):
        while self.running:
            data = self.serial_interface.read_all()
            if data:
                self.raw_received.emit(data)
                # Feed to processor and get completed packets
                packets = self.tlm_processor.feed(data)
                for pkt in packets:
                    self.packet_received.emit(pkt)
            self.msleep(10)

    def stop(self):
        self._running = False