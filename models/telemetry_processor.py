from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class TelemetryProcessor(QObject):
    packet_parsed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    SYNC = b'\xAA\xAA'

    def __init__(self):
        super().__init__()
        self.buffer = bytearray()

    @staticmethod
    def compute_crc(data: bytes) -> int:
        """
        Computes CRC-8 matching the provided CommandDispatcher::computeCRC logic.
        Polynomial: 0x07 (x^8 + x^2 + x + 1)
        Initial Value: 0xFF
        """
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x07) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    @pyqtSlot(bytes)
    def process_raw_data(self, data: bytes):
        try:
            packets = self.feed(data)
            for pkt in packets:
                self.packet_parsed.emit(pkt)
        except Exception as e:
            self.error_occurred.emit(f"Telemetry processing error: {e}")

    def feed(self, data: bytes):
        self.buffer.extend(data)
        packets = []

        while True:
            sync_index = self.buffer.find(self.SYNC)

            if sync_index == -1:
                if len(self.buffer) > 1:
                    self.buffer = self.buffer[-1:]
                else:
                    self.buffer.clear()
                break

            if sync_index > 0:
                del self.buffer[:sync_index]

            # Minimum frame:
            # SYNC(2) + TLMID(2) + TIMESTAMP(4) + LEN(1) + CRC(1) = 10 bytes minimum
            if len(self.buffer) < 10:
                break

            payload_len = self.buffer[8]
            total_frame_len = 9 + payload_len + 1

            if len(self.buffer) < total_frame_len:
                break

            frame = bytes(self.buffer[:total_frame_len])
            del self.buffer[:total_frame_len]

            tlm_id = int.from_bytes(frame[2:4], byteorder='big')
            timestamp_raw = int.from_bytes(frame[4:8], byteorder='big')
            payload = frame[9:9 + payload_len]
            received_crc = frame[-1]

            # Optional CRC check — currently not enforced
            # computed_crc = self.compute_crc(frame[:-1])
            # if computed_crc != received_crc:
            #     continue
            pkt = {
                "raw": frame,
                "tlm_id": tlm_id,
                "timestamp": timestamp_raw,
                "payload": payload,
                "length": payload_len,
                "crc": received_crc,
            }
            packets.append(pkt)

        return packets


