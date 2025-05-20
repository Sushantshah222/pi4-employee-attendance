from django.urls import path
from .views import RecordAttendance

urlpatterns = [
    path('record/', RecordAttendance.as_view(), name='record_attendance'),
]
