import time
from PyQt6.QtCore import QThread, pyqtSignal


class ReceiverThread(QThread):
    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, serial_interface):
        super().__init__()
        self.serial_interface = serial_interface
        self._running = False

    def run(self):
        self._running = True
        self.status_changed.emit("Receiver thread started.")

        while self._running:
            try:
                data = self.serial_interface.read_available()
                if data:
                    self.data_received.emit(data)
                time.sleep(0.02)
            except Exception as e:
                self.error_occurred.emit(str(e))
                break

        self.status_changed.emit("Receiver thread stopped.")

    def stop(self):
        self._running = False
