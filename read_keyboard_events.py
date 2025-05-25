# read_keyboard_events.py

import requests
import evdev
import sys
import os # Import os for environment variable

<<<<<<< Updated upstream
# --- Configuration ---
API_URL = "http://192.168.1.154:8000/api/attendance/record/"
=======
# **UPDATE THIS LINE:**
DEVICE_PATH = '/dev/input/by-id/usb-IC_Reader_IC_Reader_08FF20171101-event-kbd'
API_URL = 'http://192.168.1.154:8000/api/attendance/record/' # Replace with your Django API URL
>>>>>>> Stashed changes

# Store your token securely, e.g., as an environment variable
# For simplicity in development, you can hardcode it, but for production,
# consider environment variables or a separate config file.
# TOKEN = "YOUR_GENERATED_TOKEN_HERE" # Replace with the token you copied
# Or from an environment variable:
TOKEN = os.environ.get('RFID_API_TOKEN', '7bb41645ccc18f3dbada3dfb72e2437f1e390487') # Fallback if env var not set

# --- Event Device Setup ---
# Find your RFID scanner device
# You might need to adjust '/dev/input/by-id/...' based on your scanner's actual path
# Use `ls -l /dev/input/by-id/` to find it
try:
    # Replace with the actual device path for your RFID scanner
    # You may need to run `sudo python read_keyboard_events.py` if permissions are an issue
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    rfid_device = None
    for device in devices:
        # Adjust this check based on your scanner's name or capabilities
        if "IC Reader" in device.name: # or 'rfid' or specific product name
            rfid_device = device
            break
    if not rfid_device:
        print("RFID scanner device not found. Please check device name/path.")
        sys.exit(1)

    print(f"Connected to RFID scanner: {rfid_device.name}")

except FileNotFoundError:
    print("Error: evdev could not find input devices. Are you sure it's connected and accessible?")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred during device setup: {e}")
    sys.exit(1)

# --- Main Loop ---
def send_rfid_data(tag):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {TOKEN}" # <--- ADD THIS LINE
    }
    payload = {"rfid_tag": tag}
    print(f"Sending RFID Tag: {tag}")
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        print(f"Data sent successfully: {response.status_code} - {response.json()}")
    except requests.exceptions.HTTPError as http_err:
        print(f"Error sending data: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection Error: Is the Django server running at {API_URL}? {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout Error: Request took too long. {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected error occurred: {req_err}")

# Variables to store scanned tag
scanned_tag = ""

try:
    for event in rfid_device.read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            key_event = evdev.KeyEvent(event)
            if key_event.event.value == 1: # Key down event
                if key_event.keycode == 'KEY_ENTER':
                    if scanned_tag:
                        print(f"RFID Tag Scanned: {scanned_tag}")
                        send_rfid_data(scanned_tag)
                        scanned_tag = "" # Reset tag for next scan
                else:
                    # Map keycode to character (assuming numeric tags)
                    if hasattr(key_event.keycode, '__iter__'): # If keycode is a list
                        # This handles cases like ['KEY_KP1', 'KEY_1']
                        for kc in key_event.keycode:
                            if kc.startswith('KEY_KP') or kc.startswith('KEY_'):
                                char_code = kc.replace('KEY_KP', '').replace('KEY_', '')
                                if char_code.isdigit():
                                    scanned_tag += char_code
                                    break # Take the first digit found
                    elif key_event.keycode.startswith('KEY_KP') or key_event.keycode.startswith('KEY_'):
                        char_code = key_event.keycode.replace('KEY_KP', '').replace('KEY_', '')
                        if char_code.isdigit():
                            scanned_tag += char_code

except KeyboardInterrupt:
    print("\nExiting RFID scanner script.")
finally:
    if 'rfid_device' in locals() and rfid_device:
        rfid_device.close()