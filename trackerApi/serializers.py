# from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Workspaces, Payroll_time_period, TimeType, Work_time_period, Work, Gps, Crew, Users

"""
    User Serializer
"""
class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields= ("id", "full_name", "email", "username", "password", "admin")


"""
    TimeType Serializer    
"""
class TimeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeType
        fields = ("id", "name", "type", "pay_type", "workspace_id")

"""
    Workspace Serializer
"""
class WorkspacesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspaces
        fields = ("id", "name")

"""
    Payroll Time Period Serializer
"""
class PayrollTimePeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll_time_period
        fields = ("id","workspace_id", "user_id", "start_time", "stop_time", "start_gps", "stop_gps", "approved", "note")
"""
    Work Time Period Serializer
"""
class WorkTimePeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work_time_period
        fields = ("id", "workspace_id", "user_id", "work_id", "timetype_id", "start_time", "stop_time", "start_gps", "stop_gps", "mileage", "approved", "note")
"""
    Work Serializer
"""
class WorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields = ("id", "user_id", "name", "payroll_time_period_id", "workspace_id")


"""
    Gps Serializer
"""
class GpsSerializer(serializers.ModelSerializer):
    # gps_point = serializers.ListField(child=serializers.FloatField(), allow_empty=False)
    class Meta:
        model = Gps
        fields = ("id", "user_id", "workspace_id", "gps_point", "timestamp")

# Crew Serializer
class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "name", "active", "workspace_id", "foreman_user_id", "crew_user_ids")

"""
Active Time Serializer for Work_time_period
"""
class ActiveTimeWorkTimeSerializer(serializers.ModelSerializer):
    time_type = serializers.CharField(source='timetype.name')
    gps_point = serializers.ListField(child=serializers.FloatField(), source='start_gps')
    log_time = serializers.DateTimeField(source='start_time')
    user_name = serializers.CharField(source='user.full_name')
    user_id = serializers.CharField(source="user.id")
    class Meta:
        model = Work_time_period
        fields = ("user_id", "user_name", "gps_point", "timetype_id", "workspace_id", "time_type", "log_time")


"""
Active Time Serializer for Payroll
"""
class ActiveTimeWorkPayrollSerializer(serializers.ModelSerializer):
    gps_point = serializers.ListField(child=serializers.FloatField(), source='start_gps')
    log_time = serializers.DateTimeField(source='start_time')
    user_name = serializers.CharField(source='user.full_name')
    user_id = serializers.CharField(source="user.id")
    class Meta:
        model = Payroll_time_period
        fields = ("user_id", "user_name", "workspace_id", "log_time", "gps_point")
