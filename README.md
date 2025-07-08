# Employee Attendance System

This project provides a simple RFID based attendance tracking solution built with **Django** and intended to run on a Raspberry Pi (Pi 4).

The application exposes REST API endpoints for collecting attendance data and offers several reports through a web interface. A companion script (`read_keyboard_events.py`) reads RFID tags from an attached USB scanner and posts them to the API. When the Pi is offline, scanned tags are cached locally and synced once connectivity is restored.

## Requirements

- Python 3
- Packages listed in `requirements.txt`
- SQLite (included with Python) for development

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Apply database migrations and create a superuser account:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
3. (Optional) set an API token for the RFID script:
   ```bash
   export RFID_API_TOKEN=<your token>
   ```

## Running the Server

Start the Django development server on port `8000`:
```bash
python manage.py runserver 0.0.0.0:8000
```

## Using the RFID Reader Script

The script `read_keyboard_events.py` listens to an RFID keyboard device and posts scanned tags to `http://<server>:8000/api/attendance/record/`.

Edit the `DEVICE_PATH`, `API_URL` and `TOKEN` variables in the script (or set `RFID_API_TOKEN` in the environment). Run it with:
```bash
python read_keyboard_events.py
```
While offline, scans are stored in `attendance_cache.db` and synced periodically when connectivity returns.

A helper `start.sh` script shows how to launch the Django server and the reader together on a Pi.

## Reports

The web interface provides several reports under the `attendance/report/` URLs including general attendance, absentee and late‑comer reports. CSV export endpoints are also available.

## Development Notes

- Project settings are found in `attendance_api/settings.py`.
- Default time zone is `Asia/Kathmandu` and all hosts are allowed during development.

## Testing

There are currently no automated tests. Running `python manage.py test` should succeed once dependencies are installed.
