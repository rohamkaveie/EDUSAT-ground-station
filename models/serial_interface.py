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
        self.ser = None

    def is_connected(self) -> bool:
        return self.ser is not None and self.ser.is_open
    
    def read_all(self):
        if not self.is_connected():
            return b""
        
        return self.ser.read_all()

    def read(self, size=256):
        if not self.is_connected():
            return b""
        return self.ser.read(size)

    def write(self, data: bytes):
        if self.is_connected():
            self.ser.write(data)
