from rest_framework import serializers
from .models import Employee, AttendanceRecord
from datetime import datetime, time

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class AttendanceRecordSerializer(serializers.ModelSerializer):
    rfid_tag = serializers.CharField(write_only=True, required=False)
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = AttendanceRecord
        fields = ['employee', 'timestamp', 'attendance_type', 'rfid_tag']
        read_only_fields = ['timestamp', 'attendance_type']

    def create(self, validated_data):
        rfid_tag = validated_data.pop('rfid_tag', None)
        employee = validated_data.get('employee')

        if rfid_tag:
            try:
                employee = Employee.objects.get(rfid_tag=rfid_tag)
                validated_data['employee'] = employee
            except Employee.DoesNotExist:
                raise serializers.ValidationError({"rfid_tag": "No employee found with this RFID tag."})
        elif not employee:
             raise serializers.ValidationError({"detail": "Either 'employee' or 'rfid_tag' must be provided."})

        current_datetime = datetime.now()
        current_time = current_datetime.time()
        current_day = current_datetime.date().weekday() # 0=Monday, 5=Saturday, 6=Sunday

        # Define time windows
        STANDARD_START_TIME = time(10, 0, 0)
        CHECK_IN_END = time(10, 30, 0)
        CHECK_OUT_START = time(16, 0, 0)
        CHECK_OUT_END = time(21, 0, 0)

        attendance_type = 'UNKNOWN'

        # NEW LOGIC: Check for Saturday
        if current_day == 5: # Saturday
            attendance_type = 'UNKNOWN' # Or 'WEEKEND_SCAN' if you add that choice
        elif STANDARD_START_TIME <= current_time <= CHECK_IN_END:
            # Within check-in window (and it's a weekday)
            if current_time > STANDARD_START_TIME:
                attendance_type = 'LATE_CHECK_IN'
            else:
                attendance_type = 'CHECK_IN'
        elif CHECK_OUT_START <= current_time <= CHECK_OUT_END:
            # Within check-out window (and it's a weekday)
            attendance_type = 'CHECK_OUT'
        # If none of the above, it remains 'UNKNOWN'

        validated_data['attendance_type'] = attendance_type

        return super().create(validated_data)