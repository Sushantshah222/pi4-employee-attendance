from django.contrib import admin
from .models import AttendanceRecord, Employee

class AttendanceRecordAdmin(admin.ModelAdmin):

	list_display= ('id','employee','timestamp')
	
admin.site.register(AttendanceRecord,AttendanceRecordAdmin)


admin.site.register(Employee)


