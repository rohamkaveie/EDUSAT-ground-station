import serial
import serial.tools.list_ports


class SerialInterface:
    def __init__(self):
        self.ser = None

    @staticmethod
    def list_ports():
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port: str, baudrate: int, timeout: float = 0.1):
        if self.ser and self.ser.is_open:
            self.disconnect()

        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def is_connected(self) -> bool:
        return self.ser is not None and self.ser.is_open

    def read_available(self) -> bytes:
        if not self.is_connected():
            return b""

        count = self.ser.in_waiting
        if count > 0:
            return self.ser.read(count)
        return b""

    def write(self, data: bytes):
        if self.is_connected():
            self.ser.write(data)
