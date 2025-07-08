#!/bin/bash

# Activate virtual environment
source /home/pi0/pi4-employee-attendance/ENV/bin/activate

# Go to project folder
cd /home/pi0/pi4-employee-attendance

# Start Django server in background
python3 manage.py runserver 192.168.1.149:8000 &

# Wait for the server to be ready
sleep 10

# Start RFID reader script
python3 read_keyboard_events.py
