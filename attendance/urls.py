# from django.urls import path
# from . import views

# app_name = 'attendance'

# urlpatterns = [
#     # API Endpoint
#     path('api/attendance/record/', views.RecordAttendance.as_view(), name='record_attendance'),

#     # Report Views
#     path('report/', views.AttendanceReportView.as_view(), name='attendance_report'),
#     path('report/export-csv/', views.ExportAttendanceCSVView.as_view(), name='export_attendance_csv'),
#     path('report/absentee/', views.AbsenteeReportView.as_view(), name='absentee_report'),
#     path('report/absentee/export-csv/', views.ExportAbsenteeCSVView.as_view(), name='export_absentee_csv'),
#     path('report/late-comers/', views.LateComersReportView.as_view(), name='late_comers_report'),
#     path('report/late-comers/export-csv/', views.ExportLateComersCSVView.as_view(), name='export_late_comers_csv'),
# ]





# attendance/urls.py (COMPLETE REVISED FILE)

from django.urls import path
from . import views # Import all your views

app_name = 'attendance' # IMPORTANT for namespacing

urlpatterns = [
    # API Endpoint for RFID Scanner
    path('api/attendance/record/', views.RecordAttendance.as_view(), name='record_attendance'),

    # General Attendance Report Views
    path('report/general/', views.AttendanceReportView.as_view(), name='attendance_report'),
    path('report/general/export/csv/', views.ExportAttendanceCSVView.as_view(), name='export_attendance_csv'),

    # Absentee Report Views
    path('report/absentee/', views.AbsenteeReportView.as_view(), name='absentee_report'),
    path('report/absentee/export/csv/', views.ExportAbsenteeCSVView.as_view(), name='export_absentee_csv'),

    # Late Comers Report Views
    path('report/late-comers/', views.LateComersReportView.as_view(), name='late_comers_report'),
    path('report/late-comers/export/csv/', views.ExportLateComersCSVView.as_view(), name='export_late_comers_csv'),

    # New: Employee Daily Attendance Report
    path('report/employee-daily/', views.EmployeeDailyAttendanceReportView.as_view(), name='employee_daily_attendance_report'),
    path('report/employee-daily/export/csv/', views.ExportEmployeeDailyAttendanceCSVView.as_view(), name='export_employee_daily_attendance_csv'),

    # Add other URLs as needed for your application (e.g., employee management, etc.)
]