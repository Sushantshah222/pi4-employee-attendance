import csv
from datetime import datetime, time, date, timedelta # Consolidated datetime imports

from django.http import HttpResponse
from django.views import View
from django.shortcuts import render
from django.db.models import Q # For complex queries (OR conditions)

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
            return Response({"message": "Attendance recorded successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- General Attendance Report Views ---
class AttendanceReportView(View):
    def get(self, request):
        starting_date_str = request.GET.get('starting_date')
        ending_date_str = request.GET.get('ending_date')
        employee_query = request.GET.get('employee')

        attendance_records = AttendanceRecord.objects.all().select_related('employee')

        # Apply date range filter
        try:
            if starting_date_str:
                starting_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
                attendance_records = attendance_records.filter(timestamp__date__gte=starting_date)
            else:
                starting_date = None # No starting date provided

            if ending_date_str:
                ending_date = datetime.strptime(ending_date_str, '%Y-%m-%d').date()
                attendance_records = attendance_records.filter(timestamp__date__lte=ending_date)
            else:
                ending_date = None # No ending date provided

        except ValueError:
            # Handle bad date format gracefully
            print("Invalid date format provided for attendance report.")
            starting_date = None
            ending_date = None
            attendance_records = AttendanceRecord.objects.none() # Return empty queryset if dates are invalid

        # Apply employee filter (by name or employee_id)
        if employee_query:
            attendance_records = attendance_records.filter(
                Q(employee__name__icontains=employee_query) |
                Q(employee__employee_id__icontains=employee_query)
            )

        # Order records for display
        attendance_records = attendance_records.order_by('timestamp')

        context = {
            'attendance_records': attendance_records,
            'starting_date': starting_date,
            'ending_date': ending_date,
            'employee_query': employee_query # Pass back for template to remember input
        }
        return render(request, 'attendance/attendance_report.html', context)


class ExportAttendanceCSVView(View):
    def get(self, request):
        starting_date_str = request.GET.get('starting_date')
        ending_date_str = request.GET.get('ending_date')
        employee_query = request.GET.get('employee')

        attendance_records = AttendanceRecord.objects.all().select_related('employee')

        # Apply date range filter
        try:
            if starting_date_str:
                starting_date = datetime.strptime(starting_date_str, '%Y-%m-%d').date()
                attendance_records = attendance_records.filter(timestamp__date__gte=starting_date)

            if ending_date_str:
                ending_date = datetime.strptime(ending_date_str, '%Y- %m-%d').date()
                attendance_records = attendance_records.filter(timestamp__date__lte=ending_date)

        except ValueError:
            # If dates are invalid, do not filter by date, or return empty set
            print("Invalid date format provided for CSV export. Ignoring date filter.")
            pass # Continue without date filter, or you can set attendance_records = AttendanceRecord.objects.none()

        # Apply employee filter
        if employee_query:
            attendance_records = attendance_records.filter(
                Q(employee__name__icontains=employee_query) |
                Q(employee__employee_id__icontains=employee_query)
            )

        # Prepare CSV response
        response = HttpResponse(content_type='text/csv')
        
        # Construct a more descriptive filename based on filters
        filename_parts = []
        if starting_date_str:
            filename_parts.append(f"from_{starting_date_str}")
        if ending_date_str:
            filename_parts.append(f"to_{ending_date_str}")
        if employee_query:
            # Sanitize employee_query for filename (remove spaces, special chars)
            sanitized_employee_query = "".join(c for c in employee_query if c.isalnum() or c == '_').replace(' ', '_')
            if sanitized_employee_query:
                filename_parts.append(f"emp_{sanitized_employee_query}")

        filename = "attendance_report"
        if filename_parts:
            filename += "_" + "_".join(filename_parts)
        filename += ".csv"
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['Employee ID', 'Employee Name', 'Timestamp'])  # Write header row

        for record in attendance_records.order_by('timestamp'): # Ensure records are ordered for CSV
            writer.writerow([
                record.employee.employee_id,
                record.employee.name,
                record.timestamp.strftime('%Y-%m-%d %H:%M:%S') # Format timestamp
            ])
        return response

# --- Absentee Report Views ---
class AbsenteeReportView(View):
    def get(self, request):
        date_str = request.GET.get('date')
        report_date = None
        absent_employees = []
        is_weekend = False

        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                is_weekend = report_date.weekday() >= 5 # Check if it's a weekend (Saturday=5, Sunday=6)

                if not is_weekend: # Only consider working days for absence
                    all_employees = Employee.objects.all().order_by('name')
                    
                    # Get IDs of employees who have at least one attendance record on the report_date
                    present_employees_ids = AttendanceRecord.objects.filter(
                        timestamp__date=report_date
                    ).values_list('employee_id', flat=True).distinct()

                    # Filter all employees to find those NOT in the present_employees_ids list
                    absent_employees = all_employees.exclude(id__in=present_employees_ids)
            except ValueError:
                # Invalid date format
                print("Invalid date format provided for absentee report.")
                report_date = None

        context = {
            'absent_employees': absent_employees,
            'report_date': report_date,
            'is_weekend': is_weekend
        }
        return render(request, 'attendance/absentee_report.html', context)


class ExportAbsenteeCSVView(View):
    def get(self, request):
        date_str = request.GET.get('date')
        report_date = None
        absent_employees = []

        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if not (report_date.weekday() >= 5): # Only process if valid date and weekday
                    all_employees = Employee.objects.all()
                    present_employees_ids = AttendanceRecord.objects.filter(
                        timestamp__date=report_date
                    ).values_list('employee_id', flat=True).distinct()
                    absent_employees = all_employees.exclude(id__in=present_employees_ids)
            except ValueError:
                pass # Invalid date, no filtering will occur for this date

        response = HttpResponse(content_type='text/csv')
        filename_date = report_date.strftime('%Y-%m-%d') if report_date else "all"
        response['Content-Disposition'] = f'attachment; filename="absentee_report_{filename_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Employee ID', 'Employee Name', 'RFID Tag']) # Header

        for employee in absent_employees.order_by('name'): # Ensure ordering for CSV
            writer.writerow(
                [employee.employee_id, employee.name, employee.rfid_tag if employee.rfid_tag else ""]
            )

        return response


# --- Late Comers Report Views ---
class LateComersReportView(View):
    def get(self, request):
        date_str = request.GET.get('date')
        report_date = None
        late_comers = []
        STANDARD_START_TIME = time(9, 0, 0) # Example: 9:00 AM

        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                # Check if it's a weekday for late comers, though not strictly necessary if you want weekend late comers too
                if not (report_date.weekday() >= 5): # Only consider working days for late comers
                    all_employees = Employee.objects.all().order_by('name')
                    for employee in all_employees:
                        # Find the very first attendance record for this employee on this specific date
                        first_scan = AttendanceRecord.objects.filter(
                            employee=employee,
                            timestamp__date=report_date
                        ).order_by('timestamp').first()

                        if first_scan:
                            # Combine the report_date with the STANDARD_START_TIME for comparison
                            expected_start_datetime = datetime.combine(report_date, STANDARD_START_TIME)

                            # Compare the actual first scan time with the expected start time
                            if first_scan.timestamp > expected_start_datetime:
                                late_comers.append({
                                    'employee': employee,
                                    'first_scan_time': first_scan.timestamp
                                })
            except ValueError:
                # Invalid date format
                print("Invalid date format provided for late comers report.")
                report_date = None

        context = {
            'late_comers': late_comers,
            'report_date': report_date,
            'standard_start_time': STANDARD_START_TIME
        }
        return render(request, 'attendance/late_comers_report.html', context)


class ExportLateComersCSVView(View):
    def get(self, request):
        date_str = request.GET.get('date')
        report_date = None
        late_comers = []
        STANDARD_START_TIME = time(9, 0, 0) # Example: 9:00 AM

        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if not (report_date.weekday() >= 5): # Only process if valid date and weekday
                    all_employees = Employee.objects.all()
                    for employee in all_employees:
                        first_scan = AttendanceRecord.objects.filter(
                            employee=employee,
                            timestamp__date=report_date
                        ).order_by('timestamp').first()

                        if first_scan:
                            expected_start_datetime = datetime.combine(report_date, STANDARD_START_TIME)
                            if first_scan.timestamp > expected_start_datetime:
                                late_comers.append({
                                    'employee': employee,
                                    'first_scan_time': first_scan.timestamp
                                })
            except ValueError:
                pass # Invalid date, no filtering will occur for this date

        response = HttpResponse(content_type='text/csv')
        filename_date = report_date.strftime('%Y-%m-%d') if report_date else "all"
        response['Content-Disposition'] = f'attachment; filename="late_comers_report_{filename_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Employee ID', 'Employee Name',
                        'First Scan Time', 'Standard Start Time'])  # Header

        for record in late_comers:
            writer.writerow([
                record['employee'].employee_id,
                record['employee'].name,
                record['first_scan_time'].strftime('%Y-%m-%d %H:%M:%S'),
                STANDARD_START_TIME.strftime('%H:%M:%S')
            ])
        return response
    

    