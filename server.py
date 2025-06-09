import serial
import time
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# Edit these parameters as needed for your multimeter
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
PARITY = serial.PARITY_NONE
STOP_BITS = serial.STOPBITS_ONE
DATA_BITS = serial.EIGHTBITS
TIMEOUT = 2
HOST = "0.0.0.0"
PORT = 8000

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gurras Multimeter Voltage Display</title>
    <!-- Inspired by Matt Browns multimeter overlay -->
    <style>
        body {
            background-color: #535353;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }
        .voltage-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            text-align: center;
        }
        .voltage-display {
            color: yellow;
            font-size: 6em;
            padding: 20px;
            border-radius: 10px;
            background-color: rgba(0, 0, 0, 0.50);
        }
    </style>
</head>
<body>
    <div class="voltage-container">
        <div class="voltage-display" id="voltage">Connecting to multimeter...</div>
    </div>
    <script>
        const voltageDisplay = document.getElementById('voltage');
        async function fetchVoltage() {
            try {
                const response = await fetch('/voltage');
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.status);
                }
                const data = await response.json();
                voltageDisplay.textContent = data.voltage;
            } catch (error) {
                console.error('Error fetching voltage:', error);
                voltageDisplay.textContent = 'Error fetching voltage: ' + error.message;
            }
        }
        setInterval(fetchVoltage, 1000);
        fetchVoltage();
    </script>
</body>
</html>
"""


def initialize_serial():
    """Initialize the serial connection with fixed parameters."""
    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=TIMEOUT,
            bytesize=DATA_BITS,
            parity=PARITY,
            stopbits=STOP_BITS,
        )
        print(
            f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud, parity={PARITY}, stop bits={STOP_BITS}"
        )
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return None


def read_and_convert_multimeter(ser):
    """Send SCPI command, read response, and convert to voltage."""
    try:
        ser.write(b"MEAS?\n")
        time.sleep(0.5)
        if ser.in_waiting > 0:
            raw_data = ser.readline()
            print(f"Raw bytes from multimeter: {raw_data}")
            try:
                reading = raw_data.decode("ascii", errors="ignore").strip()
                if reading:
                    try:
                        value = float(reading)
                        voltage = value
                        print(f"Parsed voltage: {voltage:.6f} V")
                        return voltage
                    except ValueError:
                        print(f"Failed to parse reading to float: {reading}")
                        return None
            except UnicodeDecodeError:
                print(f"Failed to decode: {raw_data}")
                return None
        else:
            print("No data available in buffer")
            return None
    except serial.SerialException as e:
        print(f"Error during communication: {e}")
        return None


class VoltageHandler(BaseHTTPRequestHandler):
    def __init__(self, ser, *args, **kwargs):
        self.ser = ser
        super().__init__(*args, **kwargs)

    def do_GET(self):
        print(f"Received request for path: {self.path}")
        if self.path == "/voltage":
            voltage = read_and_convert_multimeter(self.ser)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            if voltage is not None:
                response = {"voltage": f"{voltage:.6f} V"}
                print(f"Sending voltage response: {response}")
            else:
                response = {"voltage": "Error reading voltage"}
                print(f"Sending error response: {response}")
            self.wfile.write(json.dumps(response).encode("utf-8"))
        elif self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
            print("Served HTML content for root or index.html")
        else:
            self.send_response(404)
            self.end_headers()
            print(f"404 - Path not found: {self.path}")


def run_server(ser):
    """Run HTTP server to serve voltage data and HTML."""

    def handler(*args, **kwargs):
        VoltageHandler(ser, *args, **kwargs)

    server = HTTPServer((HOST, PORT), handler)
    print(f"Server running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping the server...")
        server.server_close()
        if ser and ser.is_open:
            ser.close()
            print("Serial connection closed")


if __name__ == "__main__":
    ser = initialize_serial()
    if ser:
        run_server(ser)
