from django.urls import path
from .views import *

app_name = 'attendance'


urlpatterns = [
    path('record/', RecordAttendance.as_view(), name='record_attendance'),
    path('report/', AttendanceReportView.as_view(), name='attendance_report'),
    path('export/csv/', ExportAttendanceCSVView.as_view(), name='export_attendance_csv'),

    path('report/absentee/', AbsenteeReportView.as_view(), name='absentee_report'),
    path('export/absentee/csv/', ExportAbsenteeCSVView.as_view(), name='export_absentee_csv'),
    path('report/late-comers/', LateComersReportView.as_view(), name='late_comers_report'),
    path('export/late-comers/csv/', ExportLateComersCSVView.as_view(), name='export_late_comers_csv'),


]
