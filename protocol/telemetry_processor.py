class TelemetryProcessor:
    SYNC = b'\xAA\xAA'

    def __init__(self):
        self.buffer = bytearray()

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
                    # Polynomial 0x07 is used here
                    crc = ((crc << 1) ^ 0x07) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF

        return crc

    def feed(self, data: bytes):
        self.buffer.extend(data)
        print(self.buffer)
        packets = []

        while True:
            # 1. Look for the 2-byte SYNC: 0xAAAA
            sync_index = self.buffer.find(b'\xAA\xAA')
            
            if sync_index < 0:
                # No sync found: clear buffer except for the last byte
                # (which might be the first half of the next sync)
                if len(self.buffer) > 1:
                    self.buffer = self.buffer[-1:]
                else:
                    self.buffer.clear()
                break
                
            # Discard junk before the sync
            if sync_index > 0:
                del self.buffer[:sync_index]
            
            # 2. Need at least 7 bytes to read the header:
            # SYNC(2) + TLM_ID(2) + TIMESTAMP(4) + LEN(1) = 7 bytes
            if len(self.buffer) < 7:
                break
                
            # 3. Get the length of the data (index 6)
            payload_len = self.buffer[8]
            
            # Total frame = SYNC(2) + TLM_ID(2) + TIMESTAMP(4) + LEN(1) + payload_len + CRC(1)
            total_frame_len = 9 + payload_len + 1
            
            # 4. If we don't have the full frame, wait for more data
            if len(self.buffer) < total_frame_len:
                break
                
            # 5. Extract the full frame
            frame = bytes(self.buffer[:total_frame_len])
            
            # 6. CRC Validation (assuming your CRC logic is correct)
            # If CRC check fails, discard the first 2 bytes and re-scan
            # if not self.verify_crc(frame):
            #     del self.buffer[:2]
            #     continue

            # 7. Success: remove from buffer and parse
            del self.buffer[:total_frame_len]
            
            payload = frame[9:9+payload_len]

            tlm_id = int.from_bytes(frame[2:4], byteorder='big')

            if tlm_id != 1:
                print(frame)

            timestamp = int.from_bytes(frame[4:8], byteorder='big')
            
            
            packets.append({
                "raw": frame,
                "tlm_id": tlm_id,
                "timestamp": timestamp//1000,
                "payload": payload,
                "length": payload_len,
            })
            
        return packets

