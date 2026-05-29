from PyQt6.QtCore import QThread, pyqtSignal

class ReceiverThread(QThread):
    raw_received = pyqtSignal(bytes)
    status_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, serial_interface):
        super().__init__()
        self.serial_interface = serial_interface
        self._running = True

    def run(self):
        while self._running:
            try:
                data = self.serial_interface.read_all()
                if data:
                    self.raw_received.emit(data)
                self.msleep(100)
            except Exception as e:
                self.error_occurred.emit(str(e))
                self.msleep(200)

    def stop(self):
        self._running = False
