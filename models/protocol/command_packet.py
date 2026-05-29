SYNC_BYTE = 0xAAAA


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


def build_command_packet(opcode: bytes, args: bytes = b"") -> bytes:
    """
    Packet format:
    [SYNC][LEN][DATA...][CRC]

    DATA = [OPCODE][ARGS...]
    """

    data = opcode + args
    
    length = len(data)

    # packet = bytes([SYNC_BYTE>>8, SYNC_BYTE & 0xff, length]) + data

    packet = bytes([length]) + data

    crc = compute_crc(packet)


    packet = bytes([SYNC_BYTE>>8, SYNC_BYTE & 0xff]) + packet + bytes([crc])

    return packet
