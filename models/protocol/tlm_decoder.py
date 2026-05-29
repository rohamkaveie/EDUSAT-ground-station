import struct
import json

class TelemetryDecoder:
    def __init__(self, map_path):
        with open(map_path, 'r') as f:
            data = json.load(f)
            self.tlm = data['telemetry']
            self.events = data['events']
            self.blobs = data['blobs']

    def decode(self, packet_id, payload):
        packet_id = str(packet_id)
        # 1. Check Telemetry
        
        if packet_id in self.tlm:
            return self._decode_telemetry(self.tlm[packet_id], payload)
            
        # 2. Check Events
        elif packet_id in self.events:
            return {"type": "event", "data": self.events[packet_id]}
            
        # 3. Check Blobs
        elif packet_id in self.blobs:
            return {"type": "blob", "data": payload}
            
        return {"type": "unknown", "data": payload}

    def _decode_telemetry(self, entry, payload):
        # Generic unpacker logic based on entry['kind']
        if entry['kind'] == 'scalar':
            fmt = ">" + self._get_fmt(entry['format'])
            val = struct.unpack(fmt, payload)[0]
            # If it's an enum, look up the string
            if "enum" in entry:
                val = entry["enum"].get(str(int(val)), "UNKNOWN")
            return {"type": "telemetry", "name": entry['name'], "value": val}
            
        elif entry['kind'] == 'struct':
            # Dynamic struct unpacking
            # ... loop through fields and calculate offset ...
            return {"type": "telemetry", "name": entry['name'], "values": ...}

    def _get_fmt(self, ftype):
        return {"u8": "B", "u16": "H", "f32": "f"}.get(ftype, "B")
