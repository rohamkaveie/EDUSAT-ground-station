import os
import re
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

# Import Models
from models.serial_interface import SerialInterface
from models.receiver_thread import ReceiverThread
from models.telemetry_processor import TelemetryProcessor
from models.protocol.command_packet import build_command_packet
# from models.telemetry_forwarder import TelemetryForwarder
# from models.command_receiver import CommandReceiver

class GroundStationController(QObject):
    # Signals for the View (MainWindow) to listen to
    status_message = pyqtSignal(str)
    error_message = pyqtSignal(str)
    raw_data_received = pyqtSignal(bytes)
    packet_received = pyqtSignal(dict)
    command_fetched = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 1. Instantiate Models
        self.serial_interface = SerialInterface()
        self.telemetry_processor = TelemetryProcessor()
        # self.telemetry_forwarder = TelemetryForwarder()
        # self.command_receiver = CommandReceiver()
        self.receiver_thread = None

        # 2. Internal Signal Wiring (Data Pipeline)

        # received serial data go to telemetry_processor to get parsed
        self.raw_data_received.connect(self._handle_received_data)


        # Processed packets go to: 1. GUI (via signal) and 2. Database (Forwarder)
        self.telemetry_processor.packet_parsed.connect(self._handle_parsed_packet)
        self.telemetry_processor.error_occurred.connect(self.error_message.emit)



        # Connect Forwarder & CommandReceiver feedback to general status signals
        # self.telemetry_forwarder.status_message.connect(self.status_message.emit)
        # self.telemetry_forwarder.error_occurred.connect(self.error_message.emit)
        
        # self.command_receiver.status_messags
        self.status_message.emit("System Controller initialized.")

    # --- Connection Logic ---

    def getListPorts(self):
        return self.serial_interface.list_ports()


    def connect_serial(self, port: str, baudrate: int):
        if self.serial_interface.is_connected():
            return

        try:
            self.serial_interface.connect(port, baudrate)
            
            # Start Receiver Thread
            # We pass the processor so the thread can feed it data
            self.receiver_thread = ReceiverThread(self.serial_interface)
            
            # Connect Thread signals to Controller signals
            self.receiver_thread.raw_received.connect(self.raw_data_received.emit)
            self.receiver_thread.status_message.connect(self.status_message.emit)
            self.receiver_thread.error_occurred.connect(self.error_message.emit)
            
            self.receiver_thread.start()
            
            # Start fetching commands from server if enabled
            # if self.command_receiver.enabled and not self.command_receiver.isRunning():
            #     self.command_receiver.start()

            self.status_message.emit(f"Connected to {port}. Threads started.")

        except Exception as e:
            self.error_message.emit(f"Connection error: {e}")

    def disconnect_serial(self):
        if self.receiver_thread and self.receiver_thread.isRunning():
            self.receiver_thread.stop()
            self.receiver_thread.wait()
        
        if self.serial_interface.is_connected():
            self.serial_interface.disconnect()
        
        # if self.command_receiver.isRunning():
        #     self.command_receiver.stop()
            
        self.status_message.emit("Disconnected.")

    def is_connected(self):
        return self.serial_interface.is_connected()

    # --- Data Routing ---

    @pyqtSlot(dict)
    def _handle_parsed_packet(self, packet: dict):
        """Routes parsed data to GUI and InfluxDB."""
        # Send to View
        self.packet_received.emit(packet)
        # Send to InfluxDB
        # self.telemetry_forwarder.forward(packet)

    @pyqtSlot(bytes)
    def _handle_received_data(self, data:bytes):
        self.telemetry_processor.process_raw_data(data)

    @pyqtSlot(dict)
    def handle_server_command(self, command: dict):
        """Processes a command received from the Web Server API."""
        self.command_fetched.emit(command) # Notify GUI for the log
        
        if not self.is_connected():
            self.error_message.emit("Command received but Serial is disconnected.")
            return

        # Simple Packet Builder logic (Can be moved to a helper function)
        cmd_id = command.get("cmd_id")
        payload_hex = command.get("payload_hex", "")
        
        try:
            payload = bytes.fromhex(payload_hex) if payload_hex else b""
            # Example Structure: [SYNC 2B][CMD_ID 2B][PAYLOAD NB][CRC 1B]
            full_packet = b'\xAA\xAA' + cmd_id.to_bytes(2, 'big') + payload + b'\x0D'
            
            self.serial_interface.write(full_packet)
            self.status_message.emit(f"Sent Command ID {cmd_id} to Satellite.")
            
            # Acknowledge back to server
            if "command_id" in command:
                self.command_receiver.acknowledge_command(command["command_id"], "sent")
                
        except Exception as e:
            self.error_message.emit(f"Failed to send server command: {e}")

    def sendCommand(self, hex_text: str):

        if not self.serial_interface.is_connected():
            self.status_message.emit("Cannot send: not connected.")
            return

        try:

            clean_hex = re.sub(r'[^0-9A-Fa-f]', '', hex_text)

            if len(clean_hex) % 2 != 0:
                raise ValueError("Hex string must contain full bytes")

            cmd_opcode = bytes.fromhex(clean_hex)

            packet = build_command_packet(cmd_opcode)
            self.serial_interface.write(packet)
            self.status_message.emit(f"Sent Packet: {packet}")
        except Exception as e:
            self.error_message.emit(f"Send error: {e}")

    def cleanup(self):
        self.disconnect_serial()
        # self.telemetry_forwarder.close()
