from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from dotenv import load_dotenv
import os

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


_PRECISION_MAP = {
    "ns": WritePrecision.NS,
    "us": WritePrecision.US,
    "ms": WritePrecision.MS,
    "s":  WritePrecision.S,
}


class TelemetryForwarder(QObject):
    status_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, env_path: str = ".env"):
        super().__init__()

        # Load .env (safe to call multiple times)
        load_dotenv(env_path)

        self.url = os.getenv("INFLUX_URL", "http://localhost:8086")
        self.token = os.getenv("INFLUX_TOKEN", "")
        self.org = os.getenv("INFLUX_ORG", "")
        self.bucket = os.getenv("INFLUX_BUCKET", "")

        self.measurement = os.getenv("INFLUX_MEASUREMENT", "telemetry")
        self.satellite_id = os.getenv("INFLUX_SATELLITE_ID", "CUBESAT_01")

        precision_str = os.getenv("INFLUX_TIME_PRECISION", "ms").lower().strip()
        self.time_precision = _PRECISION_MAP.get(precision_str, WritePrecision.MS)

        self.client: InfluxDBClient | None = None
        self.write_api = None

        self._initialize_client()

    def _initialize_client(self) -> None:
        try:
            if not (self.url and self.token and self.org and self.bucket):
                raise ValueError(
                    "Missing InfluxDB config. Ensure INFLUX_URL, INFLUX_TOKEN, "
                    "INFLUX_ORG, INFLUX_BUCKET exist in .env"
                )

            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.status_message.emit(
                f"InfluxDB Forwarder initialized (bucket={self.bucket}, org={self.org})."
            )
        except Exception as e:
            self.write_api = None
            self.client = None
            self.error_occurred.emit(f"Failed to connect to InfluxDB: {e}")

    @pyqtSlot(dict)
    def forward(self, packet: dict) -> None:
        """
        Expected packet format:
          {
            "tlm_id": int | str,
            "timestamp": int,   # unix time in precision matching INFLUX_TIME_PRECISION (default ms)
            "payload": bytes | bytearray | str
          }
        """
        if not self.write_api:
            return

        try:
            tlm_id = packet.get("tlm_id", "unknown")
            ts = packet.get("timestamp", None)
            payload = packet.get("payload", b"")

            if ts is None:
                raise ValueError("packet missing required field: 'timestamp'")

            # store payload as a string field (Influx fields cannot be raw bytes)
            if isinstance(payload, (bytes, bytearray)):
                payload_str = payload.hex()
            else:
                payload_str = str(payload)

            point = (
                Point(self.measurement)
                .tag("satellite_id", self.satellite_id)
                .tag("tlm_id", str(tlm_id))
                .field("payload", payload_str)
                .time(int(ts), self.time_precision)
            )

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)

        except Exception as e:
            self.error_occurred.emit(f"InfluxDB Write Error: {e}")

    def close(self) -> None:
        try:
            if self.client:
                self.client.close()
                self.status_message.emit("InfluxDB connection closed.")
        except Exception as e:
            self.error_occurred.emit(f"Error closing InfluxDB client: {e}")
