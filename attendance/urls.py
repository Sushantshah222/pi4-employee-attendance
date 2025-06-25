from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # API Endpoint
    path('api/attendance/record/', views.RecordAttendance.as_view(), name='record_attendance'),

    # Report Views
    path('report/', views.AttendanceReportView.as_view(), name='attendance_report'),
    path('report/export-csv/', views.ExportAttendanceCSVView.as_view(), name='export_attendance_csv'),
    path('report/absentee/', views.AbsenteeReportView.as_view(), name='absentee_report'),
    path('report/absentee/export-csv/', views.ExportAbsenteeCSVView.as_view(), name='export_absentee_csv'),
    path('report/late-comers/', views.LateComersReportView.as_view(), name='late_comers_report'),
    path('report/late-comers/export-csv/', views.ExportLateComersCSVView.as_view(), name='export_late_comers_csv'),
]
