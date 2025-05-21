from django.db import models
        
        
class Employee(models.Model):
    employee_id = models.CharField(max_length=50, unique=True)  # Unique identifier for employees
    name = models.CharField(max_length=255)
    rfid_tag = models.CharField(max_length=255, unique=True, blank=True, null=True) # Assignable RFID tag
    

    def __str__(self):
        return self.name



class AttendanceRecord(models.Model):
    ATTENDANCE_CHOICES = [
        ('CHECK_IN', 'Check-in (On Time)'),
        ('LATE_CHECK_IN', 'Check-in (Late)'),
        ('CHECK_OUT', 'Check-out'),
        ('UNKNOWN', 'Unknown')
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    attendance_type = models.CharField( # <--- ENSURE THIS LINE EXISTS AND IS CORRECT
        max_length=15, # Increased max_length for 'LATE_CHECK_IN'
        choices=ATTENDANCE_CHOICES,
        default='UNKNOWN'
    )

    def __str__(self):
        return f"{self.employee.name} - {self.get_attendance_type_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['-timestamp']