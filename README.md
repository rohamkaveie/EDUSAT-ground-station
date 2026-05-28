# EDUSAT Ground Station (GS)

A Ground Station application built in Python to monitor and command the [EDUSAT](https://github.com/rohamkaveie/EDUSAT-flight-software-primary-version) satellite. This application serves as the bridge between raw radio telemetry and high-level data analytics.

## 🚀 Key Features
*   **Real-time Telemetry Parsing**: Decodes raw binary packets (`[SYNC][TLMID][TIMESTAMP][LEN][PAYLOAD]`) into human-readable JSON formats using dynamic mapping.
*   **InfluxDB Integration**: Automatically forwards processed telemetry data to an InfluxDB/Flux instance for long-term storage and Grafana visualization.
*   **Modern UI**: A clean "Royal Purple & White" interface built with PySide6 (Qt), featuring packet monitors and system health indicators.
*   **Threaded Communication**: Asynchronous serial port handling to ensure the UI remains responsive during high-frequency data bursts.
*   **Dynamic Protocol Mapping**: Easily update telemetry definitions via `telemetry_map.json` without recompiling the application.

## 🛠 Tech Stack
*   **Language**: Python 3.10+
*   **GUI Framework**: PySide6 (Qt for Python)
*   **Database**: InfluxDB (via REST API / Influx-Client)
*   **Configuration**: Dotenv (`.env`) for secure environment management
*   **Deployment**: Compiled via Nuitka for optimized executable size (<30MB)

## 📂 Project Structure
```text
EDUSAT_GS/
├── communication/   # Serial interface and background receiver threads
├── gui/            # Main window and custom UI components
├── protocol/       # Binary decoding logic and telemetry definitions
├── services/       # External integrations (InfluxDB, API Forwarders)
└── style/          # QSS stylesheets for UI customization
```

<!-- ## ⚙️ Quick Start
1.  **Clone the repo**: `git clone https://github.com/your-username/EDUSAT_GS.git`
2.  **Install dependencies**: `pip install -r requirements.txt`
3.  **Configure environment**: Create a `.env` file with your InfluxDB credentials.
4.  **Run**: `python main.py` -->
