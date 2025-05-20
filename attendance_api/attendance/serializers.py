from rest_framework import serializers
from .models import AttendanceRecord, Employee

class AttendanceRecordSerializer(serializers.Serializer):
    rfid_tag = serializers.CharField(max_length=255)

    def validate_rfid_tag(self, value):
        try:
            employee = Employee.objects.get(rfid_tag=value)
            return employee
        except Employee.DoesNotExist:
            raise serializers.ValidationError("No employee found with this RFID tag.")

    def create(self, validated_data):
        employee = validated_data['rfid_tag']  # The validated value is the Employee object
        attendance_record = AttendanceRecord.objects.create(employee=employee)
        return attendance_record

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__' # Or specify the fields you want to expose
