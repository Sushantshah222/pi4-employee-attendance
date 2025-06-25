# # attendance/views.py (COMPLETE FILE)

# import csv
# from datetime import datetime, time, date, timedelta

# from django.http import HttpResponse
# from django.views import View
# from django.shortcuts import render
# from django.db.models import Q
# from django.db.models.functions import TruncDate

# from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin # For security

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAdminUser

# from .models import AttendanceRecord, Employee
# from .serializers import AttendanceRecordSerializer

# # --- API Endpoint for RFID Scanner ---
# class RecordAttendance(APIView):
#     permission_classes = [IsAdminUser]

#     def post(self, request):
#         serializer = AttendanceRecordSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "Attendance recorded successfully", "type": serializer.instance.attendance_type}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# # --- Base Mixin for Staff/Admin Access ---
# class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
#     def test_func(self):
#         return self.request.user.is_staff # Check if the user has staff status

#     def handle_no_permission(self):
#         if not self.request.user.is_authenticated:
#             return super().handle_no_permission() # Redirect to login
#         else:
#             return render(self.request, 'attendance/access_denied.html', status=403) # Render access denied page


# # --- General Attendance Report Views ---
# class AttendanceReportView(AdminRequiredMixin, View):
#     def get(self, request):
#         starting_date_str = request.GET.get('starting_date')
#         ending_date_str = request.GET.get('ending_date')
#         employee_query = request.GET.get('employee')
#         attendance_type_filter = request.GET.get('attendance_type')

#         attendance_records = AttendanceRecord.objects.all().select_related('employee')

#         try:
#             if starting_date_str:
#                 starting_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
#                 attendance_records = attendance_records.filter(timestamp__date__gte=starting_date)
#             else:
#                 starting_date = None

#             if ending_date_str:
#                 ending_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
#                 attendance_records = attendance_records.filter(timestamp__date__lte=ending_date)
#             else:
#                 ending_date = None

#         except ValueError:
#             print("Invalid date format provided for attendance report. Ignoring date filter.")
#             starting_date = None
#             ending_date = None
#             attendance_records = AttendanceRecord.objects.none()

#         if employee_query:
#             attendance_records = attendance_records.filter(
#                 Q(employee__name__icontains=employee_query) |
#                 Q(employee__employee_id__icontains=employee_query)
#             )

#         if attendance_type_filter and attendance_type_filter != 'ALL':
#             attendance_records = attendance_records.filter(attendance_type=attendance_type_filter)

#         attendance_records = attendance_records.order_by('timestamp')

#         context = {
#             'attendance_records': attendance_records,
#             'starting_date': starting_date,
#             'ending_date': ending_date,
#             'employee_query': employee_query,
#             'attendance_type_filter': attendance_type_filter,
#             'ATTENDANCE_CHOICES': AttendanceRecord._meta.get_field('attendance_type').choices
#         }
#         return render(request, 'attendance/attendance_report.html', context)


# class ExportAttendanceCSVView(AdminRequiredMixin, View):
#     def get(self, request):
#         starting_date_str = request.GET.get('starting_date')
#         ending_date_str = request.GET.get('ending_date')
#         employee_query = request.GET.get('employee')
#         attendance_type_filter = request.GET.get('attendance_type')

#         attendance_records = AttendanceRecord.objects.all().select_related('employee')

#         try:
#             if starting_date_str:
#                 starting_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
#                 attendance_records = attendance_records.filter(timestamp__date__gte=starting_date)

#             if ending_date_str:
#                 ending_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
#                 attendance_records = attendance_records.filter(timestamp__date__lte=ending_date)

#         except ValueError:
#             print("Invalid date format provided for CSV export. Ignoring date filter.")
#             pass

#         if employee_query:
#             attendance_records = attendance_records.filter(
#                 Q(employee__name__icontains=employee_query) |
#                 Q(employee__employee_id__icontains=employee_query)
#             )

#         if attendance_type_filter and attendance_type_filter != 'ALL':
#             attendance_records = attendance_records.filter(attendance_type=attendance_type_filter)

#         response = HttpResponse(content_type='text/csv')

#         filename_parts = []
#         if starting_date_str:
#             filename_parts.append(f"from_{starting_date_str}")
#         if ending_date_str:
#             filename_parts.append(f"to_{ending_date_str}")
#         if employee_query:
#             sanitized_employee_query = "".join(c for c in employee_query if c.isalnum() or c == '_').replace(' ', '_')
#             if sanitized_employee_query:
#                 filename_parts.append(f"emp_{sanitized_employee_query}")
#         if attendance_type_filter and attendance_type_filter != 'ALL':
#             filename_parts.append(f"type_{attendance_type_filter.lower()}")

#         filename = "attendance_report"
#         if filename_parts:
#             filename += "_" + "_".join(filename_parts)
#         filename += ".csv"

#         response['Content-Disposition'] = f'attachment; filename="{filename}"'

#         writer = csv.writer(response)
#         writer.writerow(['Employee ID', 'Employee Name', 'Timestamp', 'Attendance Type'])

#         for record in attendance_records.order_by('timestamp'):
#             writer.writerow([
#                 record.employee.employee_id,
#                 record.employee.name,
#                 record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
#                 record.get_attendance_type_display()
#             ])
#         return response


# # --- Absentee Report Views ---
# class AbsenteeReportView(AdminRequiredMixin, View):
#     def get(self, request):
#         starting_date_str = request.GET.get('starting_date')
#         ending_date_str = request.GET.get('ending_date')

#         absentee_data = []
#         employees = Employee.objects.all().order_by('name')

#         try:
#             if starting_date_str:
#                 start_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
#             else:
#                 start_date = date.today()

#             if ending_date_str:
#                 end_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
#             else:
#                 end_date = date.today()

#         except ValueError:
#             print("Invalid date format provided for absentee report. Returning empty.")
#             return render(request, 'attendance/absentee_report.html', {
#                 'absentee_data': [],
#                 'starting_date': None,
#                 'ending_date': None,
#                 'error_message': 'Invalid date format provided.'
#             })

#         if start_date > end_date:
#             start_date, end_date = end_date, start_date

#         current_date_iter = start_date
#         while current_date_iter <= end_date:
#             is_weekend = (current_date_iter.weekday() == 5) # Saturday is 5

#             if not is_weekend:
#                 present_employees_ids = AttendanceRecord.objects.filter(
#                     timestamp__date=current_date_iter
#                 ).values_list('employee_id', flat=True).distinct()

#                 absent_employees_for_day = employees.exclude(id__in=present_employees_ids)

#                 absentee_data.append({
#                     'date': current_date_iter,
#                     'absent_employees': absent_employees_for_day
#                 })

#             current_date_iter += timedelta(days=1)

#         context = {
#             'absentee_data': absentee_data,
#             'starting_date': start_date,
#             'ending_date': end_date
#         }
#         return render(request, 'attendance/absentee_report.html', context)


# class ExportAbsenteeCSVView(AdminRequiredMixin, View):
#     def get(self, request):
#         starting_date_str = request.GET.get('starting_date')
#         ending_date_str = request.GET.get('ending_date')

#         response = HttpResponse(content_type='text/csv')
#         filename_parts = []

#         try:
#             if starting_date_str:
#                 start_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
#                 filename_parts.append(f"from_{starting_date_str}")
#             else:
#                 start_date = date.today()

#             if ending_date_str:
#                 end_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
#                 filename_parts.append(f"to_{ending_date_str}")
#             else:
#                 end_date = date.today()

#         except ValueError:
#             response['Content-Disposition'] = 'attachment; filename="absentee_report_invalid_dates.csv"'
#             writer = csv.writer(response)
#             writer.writerow(['Error', 'Invalid date format provided.'])
#             return response

#         if start_date > end_date:
#             start_date, end_date = end_date, start_date

#         filename = "absentee_report"
#         if filename_parts:
#             filename += "_" + "_".join(filename_parts)
#         filename += ".csv"
#         response['Content-Disposition'] = f'attachment; filename="{filename}"'

#         writer = csv.writer(response)
#         writer.writerow(['Date', 'Employee ID', 'Employee Name', 'RFID Tag'])

#         employees = Employee.objects.all().order_by('name')

#         current_date_iter = start_date
#         while current_date_iter <= end_date:
#             is_weekend = (current_date_iter.weekday() == 5)

#             if not is_weekend:
#                 present_employees_ids = AttendanceRecord.objects.filter(
#                     timestamp__date=current_date_iter
#                 ).values_list('employee_id', flat=True).distinct()

#                 absent_employees_for_day = employees.exclude(id__in=present_employees_ids)

#                 for employee in absent_employees_for_day:
#                     writer.writerow([
#                         current_date_iter.strftime('%Y-%m-%d'),
#                         employee.employee_id,
#                         employee.name,
#                         employee.rfid_tag if employee.rfid_tag else ""
#                     ])
#             current_date_iter += timedelta(days=1)
#         return response


# # --- Late Comers Report Views ---
# class LateComersReportView(AdminRequiredMixin, View):
#     def get(self, request):
#         starting_date_str = request.GET.get('starting_date')
#         ending_date_str = request.GET.get('ending_date')

#         late_comers_data = []
#         STANDARD_START_TIME_FOR_DISPLAY = time(10, 0, 0)
#         employees = Employee.objects.all().order_by('name')

#         try:
#             if starting_date_str:
#                 start_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
#             else:
#                 start_date = date.today()

#             if ending_date_str:
#                 end_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
#             else:
#                 end_date = date.today()

#         except ValueError:
#             print("Invalid date format provided for late comers report. Returning empty.")
#             return render(request, 'attendance/late_comers_report.html', {
#                 'late_comers_data': [],
#                 'starting_date': None,
#                 'ending_date': None,
#                 'standard_start_time': STANDARD_START_TIME_FOR_DISPLAY,
#                 'error_message': 'Invalid date format provided.'
#             })

#         if start_date > end_date:
#             start_date, end_date = end_date, start_date

#         current_date_iter = start_date
#         while current_date_iter <= end_date:
#             is_weekend = (current_date_iter.weekday() == 5)

#             if not is_weekend:
#                 late_comers_for_day = []
#                 for employee in employees:
#                     first_late_checkin = AttendanceRecord.objects.filter(
#                         employee=employee,
#                         timestamp__date=current_date_iter,
#                         attendance_type='LATE_CHECK_IN'
#                     ).order_by('timestamp').first()

#                     if first_late_checkin:
#                         late_comers_for_day.append({
#                             'employee': employee,
#                             'first_scan_time': first_late_checkin.timestamp,
#                             'attendance_type': first_late_checkin.get_attendance_type_display()
#                         })

#                 if late_comers_for_day:
#                     late_comers_data.append({
#                         'date': current_date_iter,
#                         'late_comers': late_comers_for_day
#                     })
#             current_date_iter += timedelta(days=1)

#         context = {
#             'late_comers_data': late_comers_data,
#             'starting_date': start_date,
#             'ending_date': end_date,
#             'standard_start_time': STANDARD_START_TIME_FOR_DISPLAY
#         }
#         return render(request, 'attendance/late_comers_report.html', context)


# class ExportLateComersCSVView(AdminRequiredMixin, View):
#     def get(self, request):
#         starting_date_str = request.GET.get('starting_date')
#         ending_date_str = request.GET.get('ending_date')

#         response = HttpResponse(content_type='text/csv')
#         filename_parts = []
#         STANDARD_START_TIME_FOR_DISPLAY = time(10, 0, 0)

#         try:
#             if starting_date_str:
#                 start_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
#                 filename_parts.append(f"from_{starting_date_str}")
#             else:
#                 start_date = date.today()

#             if ending_date_str:
#                 end_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
#                 filename_parts.append(f"to_{ending_date_str}")
#             else:
#                 end_date = date.today()

#         except ValueError:
#             response['Content-Disposition'] = 'attachment; filename="late_comers_report_invalid_dates.csv"'
#             writer = csv.writer(response)
#             writer.writerow(['Error', 'Invalid date format provided.'])
#             return response

#         if start_date > end_date:
#             start_date, end_date = end_date, start_date

#         filename = "late_comers_report"
#         if filename_parts:
#             filename += "_" + "_".join(filename_parts)
#         filename += ".csv"
#         response['Content-Disposition'] = f'attachment; filename="{filename}"'

#         writer = csv.writer(response)
#         writer.writerow(['Date', 'Employee ID', 'Employee Name', 'First Scan Time', 'Type', 'Standard Start Time'])

#         employees = Employee.objects.all().order_by('name')

#         current_date_iter = start_date
#         while current_date_iter <= end_date:
#             is_weekend = (current_date_iter.weekday() == 5)

#             if not is_weekend:
#                 for employee in employees:
#                     first_late_checkin = AttendanceRecord.objects.filter(
#                         employee=employee,
#                         timestamp__date=current_date_iter,
#                         attendance_type='LATE_CHECK_IN'
#                     ).order_by('timestamp').first()

#                     if first_late_checkin:
#                         writer.writerow([
#                             current_date_iter.strftime('%Y-%m-%d'),
#                             employee.employee_id,
#                             employee.name,
#                             first_late_checkin.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
#                             first_late_checkin.get_attendance_type_display(),
#                             STANDARD_START_TIME_FOR_DISPLAY.strftime('%H:%M:%S')
#                         ])
#             current_date_iter += timedelta(days=1)
#         return response



# attendance/views.py (COMPLETE REVISED FILE)

import csv
import calendar # Import calendar for weekday constants
from datetime import datetime, time, date, timedelta

from django.http import HttpResponse
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Max, Min
from django.db.models.functions import TruncDate # Ensure this is imported for date truncation

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin # For security

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser

from .models import AttendanceRecord, Employee
from .serializers import AttendanceRecordSerializer


# --- Configuration for Business Rules ---
# Working days: Sunday (6) to Friday (4) in Python's weekday() (Monday is 0, Sunday is 6)
# Saturday (5) is a holiday.
WORKING_WEEKDAYS = [
    calendar.MONDAY, calendar.TUESDAY, calendar.WEDNESDAY,
    calendar.THURSDAY, calendar.FRIDAY, calendar.SUNDAY
] # 0-4 and 6

# Expected check-in window
CHECK_IN_START_TIME = time(10, 0, 0) # 10:00 AM
CHECK_IN_LATE_THRESHOLD = time(10, 0, 1) # Any time after 10:00:00 will be considered late
CHECK_IN_CUTOFF_TIME = time(11, 0, 0) # 11:00 AM - if checked in after this, it's very late (still marked LATE_CHECK_IN)

# Expected check-out window (Special case: 4 PM to 9 PM)
CHECK_OUT_EARLY_THRESHOLD = time(16, 0, 0) # 4:00 PM - check out before this is early
CHECK_OUT_LATE_THRESHOLD = time(21, 0, 0) # 9:00 PM - check out after this is considered "late departure"

# --- API Endpoint for RFID Scanner ---
class RecordAttendance(APIView):
    # This permission ensures only authenticated staff/admin can post,
    # which is handled by the TokenAuthentication on the scanner side.
    permission_classes = [IsAdminUser]

    def post(self, request):
        rfid_tag = request.data.get('rfid_tag')
        if not rfid_tag:
            return Response({"error": "rfid_tag is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(rfid_tag=rfid_tag)
        except Employee.DoesNotExist:
            return Response({"error": f"No employee found with RFID tag: {rfid_tag}"}, status=status.HTTP_404_NOT_FOUND)

        current_time = datetime.now() # Use server's current time for decision
        # Ensure current_time is timezone-aware if USE_TZ=True in settings.py
        # from django.utils import timezone
        # current_time = timezone.now()

        # Determine attendance type based on rules
        attendance_type = 'UNKNOWN' # Default to unknown

        # Get latest record for this employee today
        today_start = datetime.combine(current_time.date(), time.min)
        today_end = datetime.combine(current_time.date(), time.max)
        latest_record_today = AttendanceRecord.objects.filter(
            employee=employee,
            timestamp__range=(today_start, today_end)
        ).order_by('-timestamp').first()

        # Logic to determine check-in or check-out
        if latest_record_today and latest_record_today.attendance_type in ['CHECK_IN', 'LATE_CHECK_IN']:
            # If the last record was a check-in, the next one is likely a check-out
            # Or if it's been more than X hours since last check-in, consider it new check-in?
            # For simplicity, assume alternating IN/OUT for now
            attendance_type = 'CHECK_OUT'
        else:
            # If no previous record today, or last was a check-out, it's a check-in
            attendance_type = 'CHECK_IN'
            if current_time.time() > CHECK_IN_LATE_THRESHOLD:
                attendance_type = 'LATE_CHECK_IN'

        # Create record with determined type
        record_data = {
            'employee': employee.id,
            'attendance_type': attendance_type
        }
        serializer = AttendanceRecordSerializer(data=record_data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Attendance recorded successfully", "type": serializer.instance.get_attendance_type_display()},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- Base Mixin for Staff/Admin Access ---
class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff # Check if the user has staff status

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission() # Redirect to login
        else:
            return render(self.request, 'attendance/access_denied.html', status=403) # Render access denied page


# --- General Attendance Report Views ---
class AttendanceReportView(AdminRequiredMixin, View):
    def get(self, request):
        starting_date_str = request.GET.get('starting_date')
        ending_date_str = request.GET.get('ending_date')
        employee_query = request.GET.get('employee')
        attendance_type_filter = request.GET.get('attendance_type')

        attendance_records = AttendanceRecord.objects.all().select_related('employee')

        try:
            if starting_date_str:
                starting_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
                attendance_records = attendance_records.filter(timestamp__date__gte=starting_date)
            else:
                starting_date = None

            if ending_date_str:
                ending_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
                attendance_records = attendance_records.filter(timestamp__date__lte=ending_date)
            else:
                ending_date = None

        except ValueError:
            print("Invalid date format provided for attendance report. Ignoring date filter.")
            starting_date = None
            ending_date = None
            attendance_records = AttendanceRecord.objects.none()

        if employee_query:
            attendance_records = attendance_records.filter(
                Q(employee__name__icontains=employee_query) |
                Q(employee__employee_id__icontains=employee_query)
            )

        if attendance_type_filter and attendance_type_filter != 'ALL':
            attendance_records = attendance_records.filter(attendance_type=attendance_type_filter)

        attendance_records = attendance_records.order_by('timestamp')

        context = {
            'attendance_records': attendance_records,
            'starting_date': starting_date,
            'ending_date': ending_date,
            'employee_query': employee_query,
            'attendance_type_filter': attendance_type_filter,
            'ATTENDANCE_CHOICES': AttendanceRecord._meta.get_field('attendance_type').choices
        }
        return render(request, 'attendance/attendance_report.html', context)


class ExportAttendanceCSVView(AdminRequiredMixin, View):
    def get(self, request):
        starting_date_str = request.GET.get('starting_date')
        ending_date_str = request.GET.get('ending_date')
        employee_query = request.GET.get('employee')
        attendance_type_filter = request.GET.get('attendance_type')

        attendance_records = AttendanceRecord.objects.all().select_related('employee')

        try:
            if starting_date_str:
                starting_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
                attendance_records = attendance_records.filter(timestamp__date__gte=starting_date)

            if ending_date_str:
                ending_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
                attendance_records = attendance_records.filter(timestamp__date__lte=ending_date)

        except ValueError:
            print("Invalid date format provided for CSV export. Ignoring date filter.")
            pass

        if employee_query:
            attendance_records = attendance_records.filter(
                Q(employee__name__icontains=employee_query) |
                Q(employee__employee_id__icontains=employee_query)
            )

        if attendance_type_filter and attendance_type_filter != 'ALL':
            attendance_records = attendance_records.filter(attendance_type=attendance_type_filter)

        response = HttpResponse(content_type='text/csv')

        filename_parts = []
        if starting_date_str:
            filename_parts.append(f"from_{starting_date_str}")
        if ending_date_str:
            filename_parts.append(f"to_{ending_date_str}")
        if employee_query:
            sanitized_employee_query = "".join(c for c in employee_query if c.isalnum() or c == '_').replace(' ', '_')
            if sanitized_employee_query:
                filename_parts.append(f"emp_{sanitized_employee_query}")
        if attendance_type_filter and attendance_type_filter != 'ALL':
            filename_parts.append(f"type_{attendance_type_filter.lower()}")

        filename = "attendance_report"
        if filename_parts:
            filename += "_" + "_".join(filename_parts)
        filename += ".csv"

        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['Employee ID', 'Employee Name', 'Timestamp', 'Attendance Type'])

        for record in attendance_records.order_by('timestamp'):
            writer.writerow([
                record.employee.employee_id,
                record.employee.name,
                record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                record.get_attendance_type_display()
            ])
        return response


# --- Absentee Report Views ---
class AbsenteeReportView(AdminRequiredMixin, View):
    def get(self, request):
        starting_date_str = request.GET.get('starting_date')
        ending_date_str = request.GET.get('ending_date')

        absentee_data = []
        employees = Employee.objects.all().order_by('name')

        try:
            if starting_date_str:
                start_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
            else:
                start_date = date.today()

            if ending_date_str:
                end_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
            else:
                end_date = date.today()

        except ValueError:
            print("Invalid date format provided for absentee report. Returning empty.")
            return render(request, 'attendance/absentee_report.html', {
                'absentee_data': [],
                'starting_date': None,
                'ending_date': None,
                'error_message': 'Invalid date format provided.'
            })

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        current_date_iter = start_date
        while current_date_iter <= end_date:
            # Check if it's a working day
            if current_date_iter.weekday() in WORKING_WEEKDAYS:
                present_employees_ids = AttendanceRecord.objects.filter(
                    timestamp__date=current_date_iter
                ).values_list('employee__id', flat=True).distinct() # Corrected to employee__id

                absent_employees_for_day = employees.exclude(id__in=present_employees_ids)

                absentee_data.append({
                    'date': current_date_iter,
                    'absent_employees': absent_employees_for_day
                })
            else:
                # Optionally, you can add holidays to the report explicitly
                # absentee_data.append({'date': current_date_iter, 'holiday': True})
                pass # Do nothing for weekends/holidays

            current_date_iter += timedelta(days=1)

        context = {
            'absentee_data': absentee_data,
            'starting_date': start_date,
            'ending_date': end_date
        }
        return render(request, 'attendance/absentee_report.html', context)


class ExportAbsenteeCSVView(AdminRequiredMixin, View):
    def get(self, request):
        starting_date_str = request.GET.get('starting_date')
        ending_date_str = request.GET.get('ending_date')

        response = HttpResponse(content_type='text/csv')
        filename_parts = []

        try:
            if starting_date_str:
                start_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
                filename_parts.append(f"from_{starting_date_str}")
            else:
                start_date = date.today()

            if ending_date_str:
                end_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
                filename_parts.append(f"to_{ending_date_str}")
            else:
                end_date = date.today()

        except ValueError:
            response['Content-Disposition'] = 'attachment; filename="absentee_report_invalid_dates.csv"'
            writer = csv.writer(response)
            writer.writerow(['Error', 'Invalid date format provided.'])
            return response

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        filename = "absentee_report"
        if filename_parts:
            filename += "_" + "_".join(filename_parts)
        filename += ".csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Employee ID', 'Employee Name', 'RFID Tag'])

        employees = Employee.objects.all().order_by('name')

        current_date_iter = start_date
        while current_date_iter <= end_date:
            if current_date_iter.weekday() in WORKING_WEEKDAYS: # Only check on working days
                present_employees_ids = AttendanceRecord.objects.filter(
                    timestamp__date=current_date_iter
                ).values_list('employee__id', flat=True).distinct()

                absent_employees_for_day = employees.exclude(id__in=present_employees_ids)

                for employee in absent_employees_for_day:
                    writer.writerow([
                        current_date_iter.strftime('%Y-%m-%d'),
                        employee.employee_id,
                        employee.name,
                        employee.rfid_tag if employee.rfid_tag else ""
                    ])
            current_date_iter += timedelta(days=1)
        return response


# --- Late Comers Report Views ---
class LateComersReportView(AdminRequiredMixin, View):
    def get(self, request):
        starting_date_str = request.GET.get('starting_date')
        ending_date_str = request.GET.get('ending_date')

        late_comers_data = []
        employees = Employee.objects.all().order_by('name')

        try:
            if starting_date_str:
                start_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
            else:
                start_date = date.today()

            if ending_date_str:
                end_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
            else:
                end_date = date.today()

        except ValueError:
            print("Invalid date format provided for late comers report. Returning empty.")
            return render(request, 'attendance/late_comers_report.html', {
                'late_comers_data': [],
                'starting_date': None,
                'ending_date': None,
                'standard_start_time': CHECK_IN_START_TIME, # Use the defined constant
                'error_message': 'Invalid date format provided.'
            })

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        current_date_iter = start_date
        while current_date_iter <= end_date:
            if current_date_iter.weekday() in WORKING_WEEKDAYS: # Only check on working days
                late_comers_for_day = []
                for employee in employees:
                    # Filter for 'LATE_CHECK_IN' directly based on API logic
                    first_late_checkin = AttendanceRecord.objects.filter(
                        employee=employee,
                        timestamp__date=current_date_iter,
                        attendance_type='LATE_CHECK_IN'
                    ).order_by('timestamp').first()

                    if first_late_checkin:
                        late_comers_for_day.append({
                            'employee': employee,
                            'first_scan_time': first_late_checkin.timestamp,
                            'attendance_type': first_late_checkin.get_attendance_type_display()
                        })

                if late_comers_for_day:
                    late_comers_data.append({
                        'date': current_date_iter,
                        'late_comers': late_comers_for_day
                    })
            current_date_iter += timedelta(days=1)

        context = {
            'late_comers_data': late_comers_data,
            'starting_date': start_date,
            'ending_date': end_date,
            'standard_start_time': CHECK_IN_START_TIME # Use the defined constant
        }
        return render(request, 'attendance/late_comers_report.html', context)


class ExportLateComersCSVView(AdminRequiredMixin, View):
    def get(self, request):
        starting_date_str = request.GET.get('starting_date')
        ending_date_str = request.GET.get('ending_date')

        response = HttpResponse(content_type='text/csv')
        filename_parts = []
        
        try:
            if starting_date_str:
                start_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
                filename_parts.append(f"from_{starting_date_str}")
            else:
                start_date = date.today()

            if ending_date_str:
                end_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
                filename_parts.append(f"to_{ending_date_str}")
            else:
                end_date = date.today()

        except ValueError:
            response['Content-Disposition'] = 'attachment; filename="late_comers_report_invalid_dates.csv"'
            writer = csv.writer(response)
            writer.writerow(['Error', 'Invalid date format provided.'])
            return response

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        filename = "late_comers_report"
        if filename_parts:
            filename += "_" + "_".join(filename_parts)
        filename += ".csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Employee ID', 'Employee Name', 'First Scan Time', 'Type', 'Standard Start Time'])

        employees = Employee.objects.all().order_by('name')

        current_date_iter = start_date
        while current_date_iter <= end_date:
            if current_date_iter.weekday() in WORKING_WEEKDAYS: # Only check on working days
                for employee in employees:
                    first_late_checkin = AttendanceRecord.objects.filter(
                        employee=employee,
                        timestamp__date=current_date_iter,
                        attendance_type='LATE_CHECK_IN'
                    ).order_by('timestamp').first()

                    if first_late_checkin:
                        writer.writerow([
                            current_date_iter.strftime('%Y-%m-%d'),
                            employee.employee_id,
                            employee.name,
                            first_late_checkin.timestamp.strftime('%H:%M:%S'), # Only time for first scan
                            first_late_checkin.get_attendance_type_display(),
                            CHECK_IN_START_TIME.strftime('%H:%M:%S') # Use constant
                        ])
            current_date_iter += timedelta(days=1)
        return response


# --- New: Employee Daily Attendance Report View ---
class EmployeeDailyAttendanceReportView(AdminRequiredMixin, View):
    def get(self, request):
        employee_id = request.GET.get('employee_id')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        employees = Employee.objects.all().order_by('name')
        employee = None
        attendance_data = {}
        report_summary = []
        report_context_data = { # Data to pass to template for overall summary
            'total_working_days': 0,
            'total_present_days': 0,
            'total_absent_days': 0,
            'total_late_arrivals': 0,
            'total_early_exits': 0,
            'total_late_departures': 0, # New metric
        }

        if employee_id:
            employee = get_object_or_404(Employee, id=employee_id)

            today = date.today()
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else today.replace(day=1)
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today
            except ValueError:
                return render(request, 'attendance/employee_daily_attendance_report.html', {
                    'employees': employees,
                    'error_message': 'Invalid date format provided.',
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'employee_id': employee_id
                })

            if start_date > end_date: # Swap if dates are inverted
                start_date, end_date = end_date, start_date

            # Initialize attendance status for each working day in the range
            current_day_iter = start_date
            while current_day_iter <= end_date:
                if current_day_iter.weekday() in WORKING_WEEKDAYS:
                    report_context_data['total_working_days'] += 1
                    attendance_data[current_day_iter.isoformat()] = {
                        'date': current_day_iter,
                        'present': False,
                        'check_in_time': None,
                        'check_out_time': None,
                        'late_check_in': False,
                        'early_check_out': False,
                        'late_departure': False, # New field
                        'multiple_ins': 0,
                        'multiple_outs': 0,
                    }
                current_day_iter += timedelta(days=1)

            # Fetch relevant records efficiently
            records_query = AttendanceRecord.objects.filter(
                employee=employee,
                timestamp__date__range=[start_date, end_date]
            ).order_by('timestamp')

            # Group records by date for processing
            daily_records = {}
            for record in records_query:
                record_date = record.timestamp.date()
                if record_date.isoformat() not in daily_records:
                    daily_records[record_date.isoformat()] = []
                daily_records[record_date.isoformat()].append(record)

            # Process daily records
            for iso_date, records_for_day in daily_records.items():
                if iso_date in attendance_data: # Ensure it's a working day
                    day_data = attendance_data[iso_date]
                    day_data['present'] = True
                    report_context_data['total_present_days'] += 1

                    # Get first check-in and last check-out for the day
                    check_ins = [r.timestamp for r in records_for_day if r.attendance_type in ['CHECK_IN', 'LATE_CHECK_IN']]
                    check_outs = [r.timestamp for r in records_for_day if r.attendance_type == 'CHECK_OUT']

                    if check_ins:
                        first_check_in = min(check_ins)
                        day_data['check_in_time'] = first_check_in
                        if first_check_in.time() > CHECK_IN_LATE_THRESHOLD:
                             day_data['late_check_in'] = True
                             report_context_data['total_late_arrivals'] += 1
                        # Count multiple check-ins if any
                        day_data['multiple_ins'] = len(check_ins) - 1

                    if check_outs:
                        last_check_out = max(check_outs)
                        day_data['check_out_time'] = last_check_out
                        if last_check_out.time() < CHECK_OUT_EARLY_THRESHOLD:
                            day_data['early_check_out'] = True
                            report_context_data['total_early_exits'] += 1
                        elif last_check_out.time() > CHECK_OUT_LATE_THRESHOLD: # Exited after 9 PM
                            day_data['late_departure'] = True
                            report_context_data['total_late_departures'] += 1 # Count late departures
                        # Count multiple check-outs if any
                        day_data['multiple_outs'] = len(check_outs) - 1

            # Determine truly absent days (marked in attendance_data but 'present' is False)
            for iso_date, data in attendance_data.items():
                if not data['present'] and data['date'].weekday() in WORKING_WEEKDAYS:
                    report_context_data['total_absent_days'] += 1

            # Convert to a list for template iteration
            report_summary = list(attendance_data.values())
            report_summary.sort(key=lambda x: x['date']) # Ensure chronological order

        context = {
            'employees': employees, # For the dropdown selection
            'employee': employee,
            'report_summary': report_summary,
            'start_date': start_date_str if employee_id else datetime.now().replace(day=1).strftime('%Y-%m-%d'),
            'end_date': end_date_str if employee_id else datetime.now().strftime('%Y-%m-%d'),
            'report_context_data': report_context_data, # Pass summary totals
            'CHECK_IN_START_TIME': CHECK_IN_START_TIME,
            'CHECK_IN_LATE_THRESHOLD': CHECK_IN_LATE_THRESHOLD,
            'CHECK_IN_CUTOFF_TIME': CHECK_IN_CUTOFF_TIME,
            'CHECK_OUT_EARLY_THRESHOLD': CHECK_OUT_EARLY_THRESHOLD,
            'CHECK_OUT_LATE_THRESHOLD': CHECK_OUT_LATE_THRESHOLD,
        }
        return render(request, 'attendance/employee_daily_attendance_report.html', context)


# --- New: Export Employee Daily Attendance CSV ---
class ExportEmployeeDailyAttendanceCSVView(AdminRequiredMixin, View):
    def get(self, request):
        employee_id = request.GET.get('employee_id')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if not employee_id:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="employee_daily_attendance_missing_employee.csv"'
            writer = csv.writer(response)
            writer.writerow(['Error', 'Employee ID is required for this report.'])
            return response

        employee = get_object_or_404(Employee, id=employee_id)
        
        try:
            today = date.today()
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else today.replace(day=1)
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today
        except ValueError:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="employee_daily_attendance_invalid_dates.csv"'
            writer = csv.writer(response)
            writer.writerow(['Error', 'Invalid date format provided.'])
            return response

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        response = HttpResponse(content_type='text/csv')
        filename = f"employee_daily_attendance_{employee.employee_id}_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Day', 'Status', 'Check-in Time', 'Check-out Time',
            'Late Check-in', 'Early Check-out', 'Late Departure',
            'Total IN Scans', 'Total OUT Scans'
        ])

        records_query = AttendanceRecord.objects.filter(
            employee=employee,
            timestamp__date__range=[start_date, end_date]
        ).order_by('timestamp')

        daily_records = {}
        for record in records_query:
            record_date = record.timestamp.date()
            if record_date.isoformat() not in daily_records:
                daily_records[record_date.isoformat()] = []
            daily_records[record_date.isoformat()].append(record)

        current_day_iter = start_date
        while current_day_iter <= end_date:
            day_data = {
                'date': current_day_iter,
                'present': False,
                'check_in_time': None,
                'check_out_time': None,
                'late_check_in': False,
                'early_check_out': False,
                'late_departure': False,
                'total_ins': 0,
                'total_outs': 0,
            }

            if current_day_iter.weekday() in WORKING_WEEKDAYS:
                iso_date = current_day_iter.isoformat()
                if iso_date in daily_records:
                    records_for_day = daily_records[iso_date]
                    day_data['present'] = True

                    check_ins = [r.timestamp for r in records_for_day if r.attendance_type in ['CHECK_IN', 'LATE_CHECK_IN']]
                    check_outs = [r.timestamp for r in records_for_day if r.attendance_type == 'CHECK_OUT']

                    if check_ins:
                        first_check_in = min(check_ins)
                        day_data['check_in_time'] = first_check_in
                        if first_check_in.time() > CHECK_IN_LATE_THRESHOLD:
                            day_data['late_check_in'] = True
                        day_data['total_ins'] = len(check_ins)

                    if check_outs:
                        last_check_out = max(check_outs)
                        day_data['check_out_time'] = last_check_out
                        if last_check_out.time() < CHECK_OUT_EARLY_THRESHOLD:
                            day_data['early_check_out'] = True
                        elif last_check_out.time() > CHECK_OUT_LATE_THRESHOLD:
                            day_data['late_departure'] = True
                        day_data['total_outs'] = len(check_outs)
                
                writer.writerow([
                    day_data['date'].strftime('%Y-%m-%d'),
                    day_data['date'].strftime('%A'),
                    'Present' if day_data['present'] else 'Absent',
                    day_data['check_in_time'].strftime('%H:%M:%S') if day_data['check_in_time'] else '',
                    day_data['check_out_time'].strftime('%H:%M:%S') if day_data['check_out_time'] else '',
                    'Yes' if day_data['late_check_in'] else 'No',
                    'Yes' if day_data['early_check_out'] else 'No',
                    'Yes' if day_data['late_departure'] else 'No',
                    day_data['total_ins'],
                    day_data['total_outs'],
                ])
            else: # Holiday (Saturday)
                 writer.writerow([
                    current_day_iter.strftime('%Y-%m-%d'),
                    current_day_iter.strftime('%A'),
                    'Holiday (Saturday)',
                    '', '', '', '', '', '', '' # Empty columns for non-working days
                ])


            current_day_iter += timedelta(days=1)
        return response