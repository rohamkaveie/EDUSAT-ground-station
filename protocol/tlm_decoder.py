import json

class TelemetryDecoder:
    def __init__(self, map_file="protocol/telemetry_map.json"):
        with open(map_file, 'r') as f:
            self.map = json.load(f)

    def decode(self, tlm_id, payload,timestamp):
        hex_id = f"0x{tlm_id:04X}"
        # print(self.map['telemetry'])
        # print(hex_id)

        # 1. Is it a Telemetry Variable?
        if hex_id in self.map["telemetry"]:
            # Assumption: Payload = [Value 2 bytes]
            # timestamp = int.from_bytes(payload[0:4], 'big')
            value_raw = int.from_bytes(payload, 'big')
            
            cfg = self.map["telemetry"][hex_id]
            value = value_raw * cfg["scale"]
            return "telemetry", {"name": cfg["name"], "val": f"{value:.2f} {cfg['unit']}", "time": timestamp}

        # 2. Is it an Event?
        if hex_id in self.map["events"]:
            # Assumption: Payload = [Value 1 byte]
            val = payload[0]
            msg = self.map["events"][hex_id]["message"]
            return "event", {"msg": msg, "val": val}
            
        return None, None
