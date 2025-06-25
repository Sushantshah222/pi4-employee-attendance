# attendance/admin.py

from django.contrib import admin
from .models import Employee, AttendanceRecord

# Register your models here.
admin.site.register(Employee)
admin.site.register(AttendanceRecord)