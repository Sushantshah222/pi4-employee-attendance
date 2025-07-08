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
        current_day = current_datetime.date().weekday()

        # Updated windows
        CHECK_IN_START = time(9, 30, 0)  # 9:30 AM
        CHECK_IN_END = time(11, 0, 0)    # 11:00 AM
        CHECK_OUT_START = time(16, 0, 0) # 4:00 PM
        CHECK_OUT_END = time(21, 0, 0)   # 9:00 PM

        attendance_type = 'UNKNOWN'

        if current_day == 5:  # Saturday
            attendance_type = 'UNKNOWN'
        elif CHECK_IN_START <= current_time <= CHECK_IN_END:
            if current_time <= time(11, 0, 0):
                attendance_type = 'CHECK_IN'
        elif current_time > CHECK_IN_END and current_time < CHECK_OUT_START:
            attendance_type = 'LATE_CHECK_IN'
        elif CHECK_OUT_START <= current_time <= CHECK_OUT_END:
            attendance_type = 'CHECK_OUT'

        validated_data['attendance_type'] = attendance_type

        return super().create(validated_data)
