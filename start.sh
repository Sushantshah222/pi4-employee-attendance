#!/bin/bash

# Activate your virtual environment
source /home/pi20/pi4-employee-attendance/attend/bin/activate

# Change to your project directory
cd /home/pi20/pi4-employee-attendance

# Start Django server
python3 manage.py runserver 192.168.1.123:8000 &

# Start RFID reader script
python3 read_keyboard_events.py
