from evdev import InputDevice, categorize, ecodes
import time
import requests
import json

# **UPDATE THIS LINE:**
DEVICE_PATH = '/dev/input/by-id/usb-IC_Reader_IC_Reader_08FF20171101-event-kbd'
API_URL = 'http://127.0.0.1:8000/api/attendance/record/' # Replace with your Django API URL

try:
    device = InputDevice(DEVICE_PATH)
    print(f"Connected to RFID scanner: {device.name}")

    rfid_tag = ""
    while True:
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY and event.value == 1:  # Key press event
                    key = categorize(event)
                    if key.keycode == 'KEY_ENTER':
                        if rfid_tag:
                            print(f"RFID Tag Scanned: {rfid_tag}")
                            payload = {'rfid_tag': rfid_tag}
                            headers = {'Content-Type': 'application/json'}
                            try:
                                response = requests.post(API_URL, data=json.dumps(payload), headers=headers)
                                if response.status_code == 201:
                                    print("Attendance data sent successfully!")
                                else:
                                    print(f"Error sending data: {response.status_code} - {response.text}")
                            except requests.exceptions.RequestException as e:
                                print(f"Network error: {e}")
                            rfid_tag = ""  # Reset for the next scan
                    elif 'KEY_' in key.keycode and len(key.keycode) > 4:
                        # Extract the character from KEY_A, KEY_1, etc.
                        char = key.keycode[4:].lower()
                        rfid_tag += char
                    elif key.keycode.startswith('KEY_KP') and len(key.keycode) > 6:
                        # Handle keypad numbers
                        char = key.keycode[6:]
                        rfid_tag += char
                    elif key.keycode == 'KEY_TAB':
                        # Some scanners might use TAB as a delimiter
                        if rfid_tag:
                            # Process the tag (similar to ENTER)
                            print(f"RFID Tag Scanned (Tab): {rfid_tag}")
                            # ... (send to API) ...
                            rfid_tag = ""

except FileNotFoundError:
    print(f"Error: Device not found at {DEVICE_PATH}. Make sure the path is correct.")
except PermissionError:
    print(f"Error: Permission denied to access {DEVICE_PATH}. You might need to run the script with sudo.")
except Exception as e:
    print(f"An error occurred: {e}")
