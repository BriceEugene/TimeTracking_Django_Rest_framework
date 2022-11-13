from django.db import models
from django.contrib.postgres.fields import ArrayField
from datetime import datetime
from django_postgres_timestamp_without_tz import DateTimeWithoutTZField

class Users(models.Model):
     full_name = models.CharField(max_length=255)
     email = models.CharField(unique=True, max_length=255)
     username = models.CharField(unique=True, max_length=255)
     password = models.CharField(max_length=255)
     admin = models.BooleanField(default=False)
     class Meta:
	     db_table = "users"

class Workspaces(models.Model):

     name = models.CharField(max_length=255)

     class Meta:
	     db_table = "workspaces"

class TimeType(models.Model):

     name = models.CharField(max_length=255)
     workspace = models.ForeignKey(Workspaces, on_delete=models.CASCADE, related_name="timetype")
     type = models.CharField(max_length=255)
     pay_type = models.CharField(max_length=255)
     class Meta:
	     db_table = "timetype"



class Crew(models.Model):
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=False)
    workspace = models.ForeignKey(Workspaces, on_delete=models.CASCADE, null=True, related_name="crew")
    foreman_user_id = models.IntegerField()
    crew_user_ids = ArrayField(models.IntegerField(), blank=True)
    class Meta:
	    db_table = "crew"

class Work_time_period(models.Model):
    workspace = models.ForeignKey(Workspaces, on_delete=models.CASCADE, related_name="work_time_period", null=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="worktime_period_user_id", null=True)
    work_id = models.IntegerField(null=True)
    timetype = models.ForeignKey(TimeType, on_delete=models.CASCADE, related_name="worktime_period_timetype", null=True)
    start_time = DateTimeWithoutTZField(default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), blank=True)
    stop_time = DateTimeWithoutTZField(null=True, blank=True)
    start_gps = ArrayField(models.FloatField(), null=True, blank=True)
    stop_gps = ArrayField(models.FloatField(), null=True, blank=True)
    mileage = models.CharField(max_length=255, null=True)
    approved = models.BooleanField(default=False)
    note = models.TextField(null=True)
   
    class Meta:
        db_table = "work_time_period"

class Payroll_time_period(models.Model):
    workspace = models.ForeignKey(Workspaces, on_delete=models.CASCADE, related_name="payroll_time_period", null=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="payrolltime_period_user_id", null=True)
    start_time = DateTimeWithoutTZField(default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), null=True) 
    stop_time = DateTimeWithoutTZField(null=True, blank=True)
    start_gps = ArrayField(models.FloatField(), null=True)
    stop_gps = ArrayField(models.FloatField(), null=True)
    approved = models.BooleanField(default=False)
    note = models.TextField(null=True)

    class Meta:
        db_table = "payroll_time_period"


class Gps(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="gps_user", null=True)
    # work_time_period = models.ForeignKey(Work_time_period, on_delete=models.CASCADE, null=True, related_name='gps')
    workspace = models.ForeignKey(Workspaces, on_delete=models.CASCADE, null=True, related_name='gps')
    gps_point = ArrayField(models.FloatField(), blank=True)
    timestamp = DateTimeWithoutTZField(default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), blank=True)
    # timestamp = models.IntegerField()
    class Meta:
        db_table = "gps"


class Work(models.Model):
    user_id = models.IntegerField()
    name = models.CharField(max_length=255)
    payroll_time_period = models.ForeignKey(Payroll_time_period, on_delete=models.CASCADE, null=True, related_name="work")
    workspace = models.ForeignKey(Workspaces, on_delete=models.CASCADE, related_name="work", null=True)

    class Meta:
	    db_table = "work"