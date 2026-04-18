import serial
import sys
from datetime import datetime

PORT = "/dev/ttyACM0"
BAUD_RATE = 115200

def parse_fields(line):
    fields = {}
    for part in line.replace(";", ",").split(","):
        if ":" in part:
            key, _, value = part.partition(":")
            fields[key.strip().lower()] = value.strip()
    return fields

def main():
    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    except serial.SerialException as e:
        print(f"Error opening {PORT}: {e}")
        sys.exit(1)

    print(f"Reading from {PORT} at {BAUD_RATE} baud. Press Ctrl+C to stop.\n")

    analog = None
    digital = None

    try:
        while True:
            line = ser.readline().decode("ascii", errors="replace").strip()
            if not line:
                continue

            fields = parse_fields(line)
            if "gas" in fields:
                analog = fields["gas"]
            for key in ("gas_digital", "digital", "gas_d"):
                if key in fields:
                    digital = fields[key]
                    break

            if analog is None and digital is None:
                continue

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{timestamp}  Gas analog: {analog}  Gas digital: {digital}")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
