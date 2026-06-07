# Kawasaki Ninja 7 Hybrid — Clutch Relearn Utility

A cross-platform Python utility for establishing and maintaining the UDS diagnostic session required to perform a clutch calibration/relearn procedure on the Kawasaki Ninja 7 Hybrid.

Uses a **FYSETC UCAN** adapter running [`candleLight`](https://github.com/candle-usb/candleLight_fw) firmware to send keep-alive frames over the vehicle’s CAN bus. Supports **macOS**, **Windows**, and **Linux**.

> **Note:** Any adapter running `candleLight` firmware should work in place of the FYSETC UCAN (e.g. Canable, Canable Pro, Cantact). The UCAN is simply what this procedure was developed and tested with.

-----

> ⚠️ **Disclaimer:** This is an independent, community-developed tool and is not affiliated with, endorsed by, or supported by Kawasaki Motors Corp. Use at your own risk. Performing diagnostic or calibration procedures on your vehicle’s ECU carries inherent risk, including potential damage to the transmission control system if steps are performed incorrectly or out of order. Always verify your wiring before powering on. The authors assume no liability for any damage to your vehicle, equipment, or data resulting from use of this tool.

-----

## How It Works

The script uses a sequential, deterministic timing architecture to hold the ECU in diagnostic mode throughout the entire calibration sequence:

```
[ Script ]                          [ UCAN Adapter ]                  [ Ninja 7 ECU ]
    │                                      │                                 │
    │──── 1. Diagnostic Session Request ──>│                                 │
    │     ID: 0x764  Data: 02 10 80        │──── Forward Frame ─────────────>│
    │                                      │                                 │
    │<─── 2. Session Confirmation ─────────│<─── Handshake Accepted ─────────│
    │     ID: 0x746  Data: 02 50 80        │     (Session Open)              │
    │                                      │                                 │
    │──── 3. Keep-Alive Loop (2s) ────────>│                                 │
    │     ID: 0x764  Data: 01 3E           │──── Prevents Timeout Abort ────>│
```

**Why inline timing instead of `send_periodic`?**  
Background threads can drop USB driver handles on macOS and Windows. This script handles read and write sequentially in a single loop, ensuring uninterrupted 2-second keep-alive timing with no OS-level race conditions.

-----

## Hardware & Wiring

### Required Hardware

|Item                           |Link                     |
|-------------------------------|-------------------------|
|OBD-2 Male Pigtail             |<https://a.co/d/0aG9OiDr>|
|Kawasaki → OBD-2 Female Adapter|<https://a.co/d/09srgm0J>|
|FYSETC UCAN Adapter            |<https://a.co/d/0dMtmcBJ>|

### Wiring the OBD-2 Male Pigtail to the UCAN

The Kawasaki diagnostic port uses a proprietary connector. Use the Kawasaki → OBD-2 female adapter to bridge it, then connect the OBD-2 male pigtail and wire it to the UCAN as follows:

|OBD-2 Pin|Signal  |UCAN Terminal|
|---------|--------|-------------|
|Pin 4    |Ground  |GND          |
|Pin 6    |CAN High|CANH         |
|Pin 14   |CAN Low |CANL         |

The diagnostic port is located at the **rear of the bike**. Connect the Kawasaki adapter to the diagnostic port, mate the OBD-2 pigtail to it, then connect the pigtail wires to the UCAN terminals before plugging the UCAN into your computer.

> ⚠️ **Important:** Tape off all unused OBD-2 pigtail wires individually before connecting. Exposed wires contacting each other or bare metal can cause shorts.

## Prerequisites

- **Direct USB connection** — plug the UCAN adapter directly into your host computer; avoid unpowered hubs

-----

## Installation

> **Note:** Python 3 must be installed on all platforms before proceeding. macOS additionally requires [Homebrew](https://brew.sh) (`brew`). See [python.org/downloads](https://www.python.org/downloads/) and [brew.sh](https://brew.sh) if either is not already installed.

### macOS

```bash
brew install libusb

python3 -m venv venv
source venv/bin/activate
pip install python-can gs_usb pyusb
```

### Windows

```cmd
pip install python-can gs_usb pyusb libusb
```

After installing, assign the correct kernel driver via [Zadig](https://zadig.akeo.ie/):

1. Open Zadig → **Options** → **List All Devices**
1. Select your adapter (`UCAN` or `Geschwister Schneider USB/CAN`)
1. Set the driver to **WinUSB**
1. Click **Replace Driver** (or **Install Driver**)

### Linux

```bash
pip install python-can
sudo ip link set can0 up type can bitrate 500000
```

> Linux handles `candleLight` hardware natively via SocketCAN — no userspace driver needed.

-----

## Usage

```bash
python kawasaki_clutch_relearn.py
```

The script auto-detects your OS and selects the appropriate CAN backend (`socketcan` on Linux, `gs_usb` on macOS/Windows).

-----

## Calibration Procedure

Follow these steps in order. Do not skip or reorder.

### Step 1 — Prepare the Bike

1. Confirm the engine is **OFF**
1. Turn the key switch to **ON**
1. Set the kill switch to **RUN** — the instrument cluster must be fully active

### Step 2 — Establish the Software Link

1. Run the script on your host computer
1. Wait for the session confirmation: `[RECV] Valid response captured! Data: 02 50 80 ...`
1. Leave the terminal open — closing it will drop the diagnostic session

### Step 3 — Execute the Relearn

1. **Start the engine** normally
1. Locate the **e-boost button** and **START button** on the handlebar controls
1. **Press and hold both buttons simultaneously**
1. Hold until the **boost gauge is fully illuminated**, then release both buttons
1. Wait for the boost gauge to **count down to zero** — this indicates the relearn is complete

### Step 4 — Shut Down Cleanly

1. Return to your terminal and press **`Ctrl+C`** to end the script
1. Turn the key switch to **OFF** to write the calibration values to ECU non-volatile memory

> ⚠️ **Do not power down the bike before pressing `Ctrl+C`.** The script performs a clean bus shutdown that ensures calibration data is committed correctly.

-----

## Script Reference

|Parameter          |Value   |Description                 |
|-------------------|--------|----------------------------|
|`CAN_CHANNEL`      |`0`     |Hardware channel index      |
|`CAN_BITRATE`      |`500000`|Kawasaki OBD CAN bus speed  |
|Session Request ID |`0x764` |ECU diagnostic frame address|
|Session Response ID|`0x746` |ECU acknowledgment address  |
|Keep-Alive Interval|`2.0s`  |Tester Present cadence      |

### Troubleshooting

|Symptom                      |Likely Cause                                                        |
|-----------------------------|--------------------------------------------------------------------|
|`Auto-initialization failed` |Wrong driver (Windows) or `libusb` not installed (macOS)            |
|`Timeout — no valid response`|Ignition not ON, kill switch in KILL position, or wrong CAN bitrate |
|`CAN ERROR — No ACK`         |Adapter not properly connected to OBD port, or bus termination issue|

-----

## License

LGPL-2.1 License — see [`LICENSE`](LICENSE) for full text.
