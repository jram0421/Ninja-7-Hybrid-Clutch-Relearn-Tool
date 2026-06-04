"""
Ninja 7H Clutch Relearn — Basic Test Script
--------------------------------------------
Works with any candleLight device (CANable, UCAN, etc.)
Cross-platform: Windows, macOS, Linux

Requirements:
    pip install python-can gs-usb pyusb

Windows only:
    Set driver to libusb-win32 via Zadig before first run.

Usage:
    python3 relearn_test.py           # Normal mode — connects to bike
    python3 relearn_test.py --test    # Hardware loopback via UCAN (no bike needed)
"""

import can
import time
import threading
import sys

# ── Config ────────────────────────────────────────────────────────────────────
CAN_BITRATE        = 500000
TX_ID              = 0x764
DIAG_SESSION       = [0x02, 0x10, 0x80]   # Kawasaki-specific session
TESTER_PRESENT     = [0x02, 0x3E, 0x80]   # Suppress response
KEEPALIVE_INTERVAL = 2.0
CANDLELIGHT_VID    = 0x1D50  # GS-USB compatible devices (UCAN, CANable, etc.)
CANDLELIGHT_PID    = 0x606F  # Standard GS-USB PID
# ─────────────────────────────────────────────────────────────────────────────

stop_event = threading.Event()


def find_candlelight():
    import usb.core
    print("Searching for candleLight device...")
    dev = usb.core.find(idVendor=CANDLELIGHT_VID, idProduct=CANDLELIGHT_PID)
    if dev is None:
        print("ERROR: No candleLight device found.")
        print("  - Check USB connection")
        print("  - Verify candleLight firmware is flashed")
        if sys.platform == "win32":
            print("  - Run Zadig and set driver to libusb-win32")
        elif sys.platform == "darwin":
            print("  - Run: brew install libusb")
        sys.exit(1)
    print(f"Found: {dev.product or 'candleLight device'}  Bus={dev.bus}  Addr={dev.address}")
    return dev


def open_bus(test_mode):
    dev = find_candlelight()
    print(f"Opening CAN bus {'(hardware loopback)' if test_mode else ''}...")
    return can.Bus(
        interface="gs_usb",
        channel=dev.product or "candlelight",
        bus=dev.bus,
        address=dev.address,
        bitrate=CAN_BITRATE,
        loopback=test_mode,
        receive_own_messages=test_mode
    )


def shutdown_bus(bus):
    try:
        bus.shutdown()
        print("Bus closed cleanly.")
    except Exception as e:
        print(f"Warning during shutdown: {e}")


def send(bus, data, label):
    msg = can.Message(arbitration_id=TX_ID, data=data, is_extended_id=False)
    bus.send(msg)
    print(f"  TX [{' '.join(f'{b:02X}' for b in data)}]  {label}")


def rx_loop(bus, test_mode):
    """Print received frames.
    In test mode: only show echoed TX frames (filter noise/error frames from unterminated bus).
    In normal mode: show all RX traffic including ECU responses.
    """
    while not stop_event.is_set():
        try:
            msg = bus.recv(timeout=0.5)
            if msg is not None:
                if test_mode and msg.arbitration_id != TX_ID:
                    continue  # Silently drop noise frames (e.g. 0x020 error frames)
                print(f"  RX [{' '.join(f'{b:02X}' for b in msg.data)}]  ID=0x{msg.arbitration_id:03X}  (loopback confirmed)")
        except Exception as e:
            print(f"  RX thread error: {e}")
            break


def keepalive_loop(bus):
    count = 0
    while not stop_event.is_set():
        count += 1
        try:
            send(bus, TESTER_PRESENT, f"TesterPresent #{count}")
        except Exception as e:
            print(f"\nKeepalive error: {e}")
            stop_event.set()
            break
        stop_event.wait(timeout=KEEPALIVE_INTERVAL)


def main():
    test_mode = "--test" in sys.argv

    print("=" * 45)
    print("  Ninja 7H — Clutch Relearn Test Script")
    if test_mode:
        print("  [ TEST MODE — UCAN hardware loopback ]")
    print("=" * 45)
    print()

    bus = open_bus(test_mode)
    print("Bus open.\n")

    rx_thread = threading.Thread(target=rx_loop, args=(bus, test_mode), daemon=True)
    rx_thread.start()

    try:
        input("Press ENTER to send diagnostic session request...")
        try:
            send(bus, DIAG_SESSION, "DiagnosticSession 0x80")
        except Exception as e:
            print(f"ERROR sending session request: {e}")
            shutdown_bus(bus)
            return
        time.sleep(0.2)

        print("\nStarting keepalive — Ctrl+C to stop.\n")
        ka = threading.Thread(target=keepalive_loop, args=(bus,), daemon=True)
        ka.start()

        if test_mode:
            print("Loopback active — you should see RX echo for every TX frame.\n")
        else:
            print("Perform button combo on the bike now.")
            print("Watch the instrument cluster.\n")

        # Exit main loop cleanly if keepalive thread dies
        while ka.is_alive():
            time.sleep(1)

        if not stop_event.is_set():
            print("\nKeepalive thread exited unexpectedly.")

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        stop_event.set()
        time.sleep(0.3)
        shutdown_bus(bus)
        print("Done.")


if __name__ == "__main__":
    main()
