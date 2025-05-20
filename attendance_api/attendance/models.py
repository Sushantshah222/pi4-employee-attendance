from django.db import models
        
        
class Employee(models.Model):
    employee_id = models.CharField(max_length=50, unique=True)  # Unique identifier for employees
    name = models.CharField(max_length=255)
    rfid_tag = models.CharField(max_length=255, unique=True, blank=True, null=True) # Assignable RFID tag
    

    def __str__(self):
        return self.name



class AttendanceRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE,default =1)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return f"{self.employee.name} at {self.timestamp}"
