# Ninja 7 Hybrid — Clutch Relearn Tool

Open source diagnostic tool for performing the clutch relearn procedure on the Kawasaki Ninja 7 Hybrid (2024+ MY) after an oil change, without requiring a dealer visit or proprietary software.

## Background

The Kawasaki Ninja 7 Hybrid requires a clutch relearn procedure after every oil change due to the wet clutch interacting with fresh oil viscosity. Kawasaki’s official position is that this requires the KDS (Kawasaki Diagnostic System) dealer tool. This project implements the minimal UDS diagnostic session required to hold the ECU open while the rider performs the on-bike button sequence — replacing a ~$100+ dealer visit with a $15 USB adapter and a Python script.

This project was developed in the spirit of right to repair. The DMCA (2021/2024 exemptions) explicitly permits vehicle owners to access their own diagnostic systems for maintenance purposes.

-----

## Hardware Required

- **FYSETC UCAN** (or any candleLight-compatible GS-USB CAN adapter)
- **Euro5 6-pin to OBD2 adapter cable** (ISO/DIS 19689)
- A laptop or PC (Windows or macOS)

-----

## Wiring

### Ninja 7H Diagnostic Port → UCAN

The Ninja 7 Hybrid uses a **Euro5 ISO/DIS 19689 6-pin red connector**.

```
Euro5 6-Pin        Signal        OBD2 Pin    UCAN Terminal
─────────────────────────────────────────────────────────
Pin 2          →   CAN High  →   Pin 6    →   CANH
Pin 5          →   CAN Low   →   Pin 14   →   CANL
Pin 3          →   Ground    →   Pin 4/5  →   GND (if needed)
Pin 4          →   VBAT 12V  →   Pin 16   →   (not used)
Pin 6          →   K-Line    →   Pin 7    →   (not used)
Pin 1          →   —         →   —        →   (not used)
```

If using a pre-made Euro5 → OBD2 adapter cable, connect the UCAN screw terminals to the OBD2 end:

- **CANH** → OBD2 Pin 6
- **CANL** → OBD2 Pin 14

The UCAN has onboard termination resistors (2x 59Ω = ~118Ω) enabled by default, which satisfies the CAN bus 120Ω termination requirement.

-----

## Protocol

Communication uses UDS (ISO 14229) over CAN at **500kbps**.

|Direction      |CAN ID |
|---------------|-------|
|Tool → ECU (TX)|`0x764`|
|ECU → Tool (RX)|`0x746`|

### Frames Sent

|Step|Frame     |Meaning                                                 |
|----|----------|--------------------------------------------------------|
|1   |`02 10 80`|DiagnosticSessionControl — Kawasaki-specific session    |
|2   |`02 3E 80`|TesterPresent (suppress response) — sent every 2 seconds|

The relearn sequence itself is performed on the bike via the instrument cluster and button combo. The script holds the diagnostic session open while you complete it.

-----

## Software Setup

### Dependencies

```
python-can
gs-usb
pyusb
```

Install via pip:

```bash
pip install python-can gs-usb pyusb
```

Or using the included requirements file:

```bash
pip install -r requirements.txt
```

### Windows — Driver Setup (one-time)

1. Download and run [Zadig](https://zadig.akeo.ie/)
1. Plug in the UCAN via USB
1. Select the UCAN device from the dropdown
1. Set the driver to **libusb-win32**
1. Click Install Driver

### macOS — Setup

```bash
brew install libusb
pip install python-can gs-usb pyusb
```

On macOS, `sudo` is required to access USB devices:

```bash
sudo python3 relearn.py
```

#### macOS — Virtual Environment (recommended)

```bash
python3 -m venv ~/ninja7h-venv
source ~/ninja7h-venv/bin/activate
pip install python-can gs-usb pyusb
sudo ~/ninja7h-venv/bin/python relearn.py
```

-----

## Usage

### Test Mode (UCAN connected, no bike required)

Verifies the UCAN is detected and frames can be sent. Uses hardware loopback — no bike or termination resistor needed.

```bash
python3 relearn.py --test
```

Expected output:

```
Found: UCAN USB to CAN adapter  Bus=1  Addr=1
Opening CAN bus (hardware loopback)...
Bus open.

Press ENTER to send diagnostic session request...
  TX [02 10 80]  DiagnosticSession 0x80
  RX [02 10 80]  ID=0x764  (loopback confirmed)

Starting keepalive — Ctrl+C to stop.
  TX [02 3E 80]  TesterPresent #1
  RX [02 3E 80]  ID=0x764  (loopback confirmed)
```

### Live Mode (connected to bike)

```bash
python3 relearn.py
```

1. Connect UCAN CANH/CANL to the bike’s diagnostic port via the Euro5 adapter
1. Turn the bike on (do not start engine)
1. Run the script
1. Press ENTER when prompted to open the diagnostic session
1. Perform the button combo on the bike and follow the instrument cluster prompts
1. Press Ctrl+C when the relearn is complete

-----

## Files

| File | Description |
|------|-------------|
| `relearn.py` | Clutch relearn utility |
| `LICENSE.txt` | MIT license |
| `requirements.txt` | Python dependencies |

-----

## Disclaimer

This tool is provided for personal vehicle maintenance use only. Use at your own risk. The authors are not responsible for any damage to your vehicle or ECU. This tool does not flash firmware, modify ECU calibration, or write any data to the vehicle — it only opens a read/diagnostic session and sends keepalive frames.

This project is not affiliated with or endorsed by Kawasaki Motors Corporation.

-----

## License

MIT License — see `LICENSE` for details.
