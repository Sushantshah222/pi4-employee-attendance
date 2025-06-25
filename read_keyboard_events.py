import requests
import evdev
import sys
import os
import time
import json
import sqlite3
import threading # For background syncing
import socket # For internet connectivity check
from evdev import InputDevice, categorize, ecodes

# --- Configuration ---
DEVICE_PATH = '/dev/input/by-id/usb-IC_Reader_IC_Reader_08FF20171101-event-kbd'
API_URL = 'http://192.168.1.123:8000/api/attendance/record/' # Replace with your Django API URL
TOKEN = os.environ.get('RFID_API_TOKEN', 'eeff5e0ee72f42cc33a330b78be5cfd289278194') # Replace or set env var

# SQLite Database Path
DB_PATH = 'attendance_cache.db'

# Syncing Interval (how often to check for internet and try to sync)
SYNC_INTERVAL_SECONDS = 60 # Check every 60 seconds

# --- SQLite Database Functions ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cached_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rfid_tag TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print(f"DEBUG: SQLite database initialized at {DB_PATH}")

def add_cached_tag(tag):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cached_tags (rfid_tag) VALUES (?)", (tag,))
    conn.commit()
    conn.close()
    print(f"DEBUG: RFID Tag '{tag}' cached locally.")

def get_cached_tags():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, rfid_tag FROM cached_tags ORDER BY timestamp ASC")
    tags = cursor.fetchall()
    conn.close()
    return tags

def delete_cached_tag(tag_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cached_tags WHERE id = ?", (tag_id,))
    conn.commit()
    conn.close()
    print(f"DEBUG: Cached tag ID {tag_id} deleted after successful sync.")

# --- Internet Connectivity Check ---
def is_internet_available(host="8.8.8.8", port=53, timeout=3):
    """
    Checks if internet is available by trying to connect to a well-known host (Google DNS).
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        print("DEBUG: Internet connection available.")
        return True
    except socket.error as ex:
        print(f"DEBUG: Internet connection NOT available: {ex}")
        return False

# --- API Sending Function ---
def send_rfid_data(tag, is_cached=False):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {TOKEN}"
    }
    payload = {"rfid_tag": tag}
    status_prefix = "Cached tag" if is_cached else "Scanned tag"
    print(f"Sending {status_prefix}: {tag}")
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=10) # Increased timeout
        response.raise_for_status() # Raise an exception for 4xx or 5xx status codes
        print(f"Data sent successfully: {response.status_code} - {response.json()}")
        return True # Indicate success
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Network Error for {status_prefix}: {conn_err}. Caching for retry.")
        return False # Indicate network failure
    except requests.exceptions.HTTPError as http_err:
        # For HTTP errors (like 403 Forbidden, 404 Not Found), don't cache for retry.
        # These are usually configuration issues, not temporary network problems.
        print(f"API Error for {status_prefix}: HTTP {response.status_code} - {response.text}. Not caching for retry.")
        return True # Treat as "handled", so don't re-cache/keep trying
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout Error for {status_prefix}: {timeout_err}. Caching for retry.")
        return False # Indicate network failure
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected request error for {status_prefix}: {req_err}. Not caching for retry.")
        return True # Treat as handled, not typically a network retry case
    except Exception as e:
        print(f"An unhandled error occurred during API call for {status_prefix}: {e}. Not caching for retry.")
        return True # Treat as handled

# --- Syncing Thread Function ---
def sync_cached_data():
    while True:
        time.sleep(SYNC_INTERVAL_SECONDS)
        print("\nDEBUG: Attempting to sync cached data...")
        if is_internet_available():
            cached_tags = get_cached_tags()
            if cached_tags:
                print(f"DEBUG: Found {len(cached_tags)} tags to sync.")
                for tag_id, rfid_tag in list(cached_tags): # Use list to iterate while modifying
                    print(f"DEBUG: Attempting to send cached tag ID {tag_id}: {rfid_tag}")
                    if send_rfid_data(rfid_tag, is_cached=True):
                        delete_cached_tag(tag_id)
                    else:
                        print(f"DEBUG: Failed to send cached tag {rfid_tag}. Will retry later.")
                        # If sending failed (e.g., network again), break and retry all later
                        break
            else:
                print("DEBUG: No cached tags to sync.")
        else:
            print("DEBUG: Internet not available. Cannot sync cached data.")

# --- Main Program Setup ---
# Initialize the database when the script starts
init_db()

# Start the syncing thread
sync_thread = threading.Thread(target=sync_cached_data, daemon=True) # daemon=True means thread exits with main program
sync_thread.start()
print("DEBUG: Syncing thread started.")

# --- Event Device Setup ---
device = None # Initialize device to None
try:
    device = evdev.InputDevice(DEVICE_PATH)
    device.grab() # Grab the device for exclusive access, highly recommended for input devices
    print(f"Connected to RFID scanner: {device.name}")
except FileNotFoundError:
    print(f"Error: Device not found at {DEVICE_PATH}. Make sure the path is correct.")
    sys.exit(1)
except PermissionError:
    print(f"Error: Permission denied to access {DEVICE_PATH}. You might need to run the script with sudo.")
    sys.exit(1)
except OSError as e:
    if "Device or resource busy" in str(e):
        print(f"Error: {DEVICE_PATH} is busy. Another process (like another instance of this script or evtest) might be using it.")
        print("Please ensure only one instance of the script is running and no other programs are accessing the device.")
    else:
        print(f"An OS error occurred during device setup: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred during device setup: {e}")
    sys.exit(1)

# --- Main Loop ---
rfid_tag = ""
print("Waiting for RFID scans...")
try:
    for event in device.read_loop():
        if event.type == ecodes.EV_KEY and event.value == 1:  # Key press (down) event
            key = categorize(event)
            if key.keycode == 'KEY_ENTER':
                if rfid_tag:
                    print(f"RFID Tag Scanned: {rfid_tag}")
                    # Attempt to send immediately
                    if not send_rfid_data(rfid_tag): # If immediate send fails due to network
                        add_cached_tag(rfid_tag) # Cache it
                    rfid_tag = ""  # Reset for the next scan
                else:
                    print("DEBUG: ENTER pressed, but scanned_tag is empty. Ignoring.")
            elif key.keycode.startswith('KEY_') and len(key.keycode) > 4:
                char = key.keycode[4:]
                if char.isdigit(): # Assuming RFID tags are purely numeric
                    rfid_tag += char
                    # print(f"DEBUG: Added '{char}'. Current scanned_tag: '{rfid_tag}'") # Uncomment for detailed digit debugging
            elif key.keycode.startswith('KEY_KP') and len(key.keycode) > 6:
                char = key.keycode[6:]
                if char.isdigit(): # Assuming RFID tags are purely numeric
                    rfid_tag += char
                    # print(f"DEBUG: Added '{char}'. Current scanned_tag: '{rfid_tag}'") # Uncomment for detailed digit debugging

except KeyboardInterrupt:
    print("\nExiting RFID scanner script.")
finally:
    if device:
        try:
            device.ungrab() # Release the device
            device.close()
            print("RFID scanner device released and closed.")
        except Exception as e:
            print(f"Error releasing/closing device: {e}")