import csv
from datetime import datetime, time, date, timedelta

from django.http import HttpResponse
from django.views import View
from django.shortcuts import render
from django.db.models import Q
from django.db.models.functions import TruncDate

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import AttendanceRecord, Employee
from .serializers import AttendanceRecordSerializer

# --- API Endpoint for RFID Scanner ---
class RecordAttendance(APIView):
    def post(self, request):
        serializer = AttendanceRecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Attendance recorded successfully", "type": serializer.instance.attendance_type}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- General Attendance Report Views (No functional changes here) ---
class AttendanceReportView(View):
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
            # CHANGE THIS LINE:
            'ATTENDANCE_CHOICES': AttendanceRecord._meta.get_field('attendance_type').choices
        }
        return render(request, 'attendance/attendance_report.html', context)


class ExportAttendanceCSVView(View):
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


# --- Absentee Report Views (MAJOR CHANGES FOR DATE RANGE AND WEEKEND) ---
class AbsenteeReportView(View):
    def get(self, request):
        starting_date_str = request.GET.get('starting_date')
        ending_date_str = request.GET.get('ending_date')

        absentee_data = []
        employees = Employee.objects.all().order_by('name')

        try:
            if starting_date_str:
                start_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
            else:
                start_date = date.today() # Default to today if no start date

            if ending_date_str:
                end_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
            else:
                end_date = date.today() # Default to today if no end date

        except ValueError:
            print("Invalid date format provided for absentee report. Returning empty.")
            return render(request, 'attendance/absentee_report.html', {
                'absentee_data': [],
                'starting_date': None,
                'ending_date': None,
                'error_message': 'Invalid date format provided.'
            })

        # Ensure start_date is not after end_date
        if start_date > end_date:
            start_date, end_date = end_date, start_date # Swap if out of order

        current_date_iter = start_date
        while current_date_iter <= end_date:
            is_weekend = (current_date_iter.weekday() == 5) # Saturday is 5

            if not is_weekend:
                # Get IDs of employees who have at least one attendance record (of any type) on the current_date_iter
                present_employees_ids = AttendanceRecord.objects.filter(
                    timestamp__date=current_date_iter
                ).values_list('employee_id', flat=True).distinct()

                absent_employees_for_day = employees.exclude(id__in=present_employees_ids)

                absentee_data.append({
                    'date': current_date_iter,
                    'absent_employees': absent_employees_for_day
                })
            # else: skip weekend days, don't add them to absentee_data

            current_date_iter += timedelta(days=1)

        context = {
            'absentee_data': absentee_data,
            'starting_date': start_date,
            'ending_date': end_date
        }
        return render(request, 'attendance/absentee_report.html', context)


class ExportAbsenteeCSVView(View):
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
            start_date, end_date = end_date, start_date # Swap

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
            is_weekend = (current_date_iter.weekday() == 5) # Saturday is 5

            if not is_weekend:
                present_employees_ids = AttendanceRecord.objects.filter(
                    timestamp__date=current_date_iter
                ).values_list('employee_id', flat=True).distinct()

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


# --- Late Comers Report Views (MAJOR CHANGES FOR DATE RANGE AND WEEKEND) ---
class LateComersReportView(View):
    def get(self, request):
        starting_date_str = request.GET.get('starting_date')
        ending_date_str = request.GET.get('ending_date')

        late_comers_data = []
        STANDARD_START_TIME_FOR_DISPLAY = time(10, 0, 0)
        employees = Employee.objects.all().order_by('name')

        try:
            if starting_date_str:
                start_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
            else:
                start_date = date.today() # Default to today if no start date

            if ending_date_str:
                end_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
            else:
                end_date = date.today() # Default to today if no end date

        except ValueError:
            print("Invalid date format provided for late comers report. Returning empty.")
            return render(request, 'attendance/late_comers_report.html', {
                'late_comers_data': [],
                'starting_date': None,
                'ending_date': None,
                'standard_start_time': STANDARD_START_TIME_FOR_DISPLAY,
                'error_message': 'Invalid date format provided.'
            })

        if start_date > end_date:
            start_date, end_date = end_date, start_date # Swap

        current_date_iter = start_date
        while current_date_iter <= end_date:
            is_weekend = (current_date_iter.weekday() == 5) # Saturday is 5

            if not is_weekend:
                late_comers_for_day = []
                for employee in employees:
                    first_late_checkin = AttendanceRecord.objects.filter(
                        employee=employee,
                        timestamp__date=current_date_iter,
                        attendance_type='LATE_CHECK_IN' # Filter directly for LATE_CHECK_IN
                    ).order_by('timestamp').first()

                    if first_late_checkin:
                        late_comers_for_day.append({
                            'employee': employee,
                            'first_scan_time': first_late_checkin.timestamp,
                            'attendance_type': first_late_checkin.get_attendance_type_display()
                        })
                
                if late_comers_for_day: # Only add if there are late comers for this day
                    late_comers_data.append({
                        'date': current_date_iter,
                        'late_comers': late_comers_for_day
                    })
            current_date_iter += timedelta(days=1)

        context = {
            'late_comers_data': late_comers_data,
            'starting_date': start_date,
            'ending_date': end_date,
            'standard_start_time': STANDARD_START_TIME_FOR_DISPLAY
        }
        return render(request, 'attendance/late_comers_report.html', context)


class ExportLateComersCSVView(View):
    def get(self, request):
        starting_date_str = request.GET.get('starting_date')
        ending_date_str = request.GET.get('ending_date')

        response = HttpResponse(content_type='text/csv')
        filename_parts = []
        STANDARD_START_TIME_FOR_DISPLAY = time(10, 0, 0)

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
            start_date, end_date = end_date, start_date # Swap

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
            is_weekend = (current_date_iter.weekday() == 5) # Saturday is 5

            if not is_weekend:
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
                            first_late_checkin.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            first_late_checkin.get_attendance_type_display(),
                            STANDARD_START_TIME_FOR_DISPLAY.strftime('%H:%M:%S')
                        ])
            current_date_iter += timedelta(days=1)
        return response