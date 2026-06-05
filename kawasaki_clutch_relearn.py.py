import can
import time
import sys

# --- CROSS-PLATFORM CONFIGURATION ---
CAN_CHANNEL = 0          
CAN_BITRATE = 500000     

def initialize_bus():
    """Initializes the CAN bus based on the host Operating System."""
    tp = sys.platform
    print(f"Detected Operating System: {tp}")
    
    try:
        if tp == "linux":
            # Linux handles candleLight devices via native SocketCAN kernel space
            print(f"Connecting via Linux SocketCAN (interface='socketcan', channel='can{CAN_CHANNEL}')...")
            return can.interface.Bus(interface='socketcan', channel=f'can{CAN_CHANNEL}', bitrate=CAN_BITRATE)
            
        elif tp in ("darwin", "win32"):
            # BOTH macOS and Windows utilize the cross-platform 'gs_usb' backend
            print(f"Connecting via USB abstraction layer (interface='gs_usb', channel={CAN_CHANNEL})...")
            return can.interface.Bus(interface='gs_usb', channel=CAN_CHANNEL, bitrate=CAN_BITRATE)
            
        else:
            print("Unknown OS structure. Attempting general fallback configuration...")
            return can.interface.Bus(channel=CAN_CHANNEL, bitrate=CAN_BITRATE)
            
    except Exception as e:
        print(f"\n[ERROR] Auto-initialization failed: {e}")
        print("\n💡 OS-Specific Verification Checklist:")
        print("  - MAC: Ensure 'brew install libusb' has been executed.")
        print("  - LINUX: Verify your link state: 'sudo ip link set can0 up type can bitrate 500000'")
        print("  - WINDOWS: Missing libusb-1.0.dll? Download the binary or install 'libusb' via pip.")
        sys.exit(1)

def main():
    bus = initialize_bus()
    print("Successfully connected to the UCAN adapter.\n")

    # [The rest of the sequential diagnostic & inline loop code remains exactly the same]
    init_msg = can.Message(arbitration_id=0x764, data=[0x02, 0x10, 0x80], is_extended_id=False)
    try:
        bus.send(init_msg)
        print(f"[SENT] ID: 0x764 | Data: {init_msg.data.hex(' ')}")
    except can.CanError as e:
        print(f"[ERROR] Failed to send initial message: {e}")
        bus.shutdown()
        sys.exit(1)

    print("Watching for response ID: 0x746...")
    response_received = False
    timeout = 10.0  
    start_time = time.time()

    while time.time() - start_time < timeout:
        msg = bus.recv(1.0) 
        if msg and msg.arbitration_id == 0x746:
            if len(msg.data) >= 3 and msg.data[0:3] == bytearray([0x02, 0x50, 0x80]):
                print(f"[RECV] Valid response captured! Data: {msg.data.hex(' ')}\n")
                response_received = True
                break
    
    if not response_received:
        print("[ERROR] Timeout reached. No valid response received.")
        bus.shutdown()
        sys.exit(1)

    tester_present_msg = can.Message(arbitration_id=0x764, data=[0x01, 0x3E], is_extended_id=False)
    print("[INFO] Starting inline Tester Present loop (every 2.0 seconds). Press Ctrl+C to stop.\n")
    last_send_time = 0 

    try:
        while True:
            current_time = time.time()
            if current_time - last_send_time >= 2.0:
                try:
                    bus.send(tester_present_msg)
                    print(f"[SENT Tester Present] {tester_present_msg.data.hex(' ')} | {time.strftime('%H:%M:%S')}")
                    last_send_time = current_time
                except can.CanOperationError as e:
                    print(f"\n[CAN ERROR] Message dropped (Bus full/No ACK). Details: {e}")
                    time.sleep(1)

            incoming = bus.recv(0.1)
            if incoming:
                print(f"[BUS] ID: {hex(incoming.arbitration_id)} | Data: {incoming.data.hex(' ')}")

    except KeyboardInterrupt:
        print("\n[INFO] Script stopped by user.")
    finally:
        bus.shutdown()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()