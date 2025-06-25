# attendance/models.py

from django.db import models
from datetime import time # Import time for default check-in time if needed

class Employee(models.Model):
    employee_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    rfid_tag = models.CharField(max_length=50, unique=True, blank=True, null=True)
    # You might add fields like 'department', 'position', 'email', etc.

    def __str__(self):
        return f"{self.name} ({self.employee_id})"

    class Meta:
        ordering = ['name'] # Order employees by name by default

class AttendanceRecord(models.Model):
    ATTENDANCE_CHOICES = [
        ('CHECK_IN', 'Check-in (On Time)'),
        ('LATE_CHECK_IN', 'Check-in (Late)'), # Added this choice
        ('CHECK_OUT', 'Check-out'),
        ('UNKNOWN', 'Unknown')
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    attendance_type = models.CharField(
        max_length=15, # Increased max_length to accommodate 'LATE_CHECK_IN'
        choices=ATTENDANCE_CHOICES,
        default='UNKNOWN'
    )

    def __str__(self):
        return f"{self.employee.name} - {self.get_attendance_type_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['-timestamp'] # Order records by newest first