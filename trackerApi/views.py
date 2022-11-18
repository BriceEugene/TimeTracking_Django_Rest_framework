from django.http import JsonResponse
from django.db.models import Q, Sum, F, Case, Value, When
from django.db.models.functions import  Round
from datetime import datetime, timezone
from dateutil.parser import parse
from rest_framework.views import APIView
from .models import Payroll_time_period, TimeType, Workspaces, Work_time_period, Work, Gps, Crew, Users
from .serializers import *
from .utility import Epoch, distance, download_excel, make_json
from django_postgres_timestamp_without_tz import DateTimeWithoutTZField
import os
import glob
import  jpype
import asposecells
jpype.startJVM()
from asposecells.api import Workbook, SaveFormat

class WorkspacesView(APIView):
    """
    Workspaces view class
    """
    def get(self, request):
        name = request.query_params.get("name", None)
        if name:
            queryset = Workspaces.objects.filter(name=name)
        else:
            queryset = Workspaces.objects.all()
        workspaces_serializer = WorkspacesSerializer(queryset, many=True)

        return JsonResponse(workspaces_serializer.data, safe=False)

    # POST
    def post(self, request):
        serializer = WorkspacesSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, safe=False)
        return JsonResponse(serializer.errors, safe=False)

    # PATCH
    def patch(self, request):
        id = request.query_params.get("id", None)
        try:
            workspace = Workspaces.objects.get(id=id)
            serializer = WorkspacesSerializer(workspace, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(serializer.data, safe=False)
            return JsonResponse(serializer.errors, safe=False)

        except Exception as e:
            return JsonResponse(str(e), safe=False)

class TimeTypeView(APIView):
    """
        TimeType View Class
        This is to set the types of time that can be logged for a work time period.
    """
    def get(self, request):
        queryset = TimeType.objects.all()
        workspace_id = request.query_params.get('workspace_id', None)

        if workspace_id is not None :
            queryset = queryset.filter(workspace_id=workspace_id)
        
        timetype_serializer = TimeTypeSerializer(queryset, many=True)

        return JsonResponse(timetype_serializer.data, safe=False)

    def post(self, request):
        try:
            workspace_id = request.data.get("workspace_id", None)
            workspace = Workspaces.objects.get(id=workspace_id)
            serializer = TimeTypeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(workspace=workspace)
                return JsonResponse(serializer.data, safe=False)
            return  JsonResponse(serializer.errors, safe=False)
        except Exception as e:
            return JsonResponse(str(e), safe=False)
    # @dev confirm the URL 
    def patch(self, request):
        id = request.query_params.get("id", None)
        try:
            timetype = TimeType.objects.get(id=id)
            serializer = TimeTypeSerializer(timetype, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(serializer.data, safe=False)
            return JsonResponse(serializer.errors, safe=False)                
        except Exception as e:
            return JsonResponse(str(e), safe=False)
        
class GpsView(APIView):
    '''
        Gps View Class
        This is to report the users coordinates while they are logging time
    '''
    def get(self, request):
        queryset = Gps.objects.all()
        for row in queryset:
            if row.timestamp:
                row.timestamp = row.timestamp.replace(tzinfo=timezone.utc).timestamp()
        serializer = GpsViewSerializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)

    # @dev gps_point shows invalid parameter
    def post(self, request):
        # query filter
        try:
            workspace_id = request.data.get("workspace_id", None)
            user_id = request.data.get("user_id", None)
            workspace = Workspaces.objects.get(id=workspace_id)
            user = Users.objects.get(id=user_id)
            data = request.data.copy()
            if request.data.get("timestamp"):
                data["timestamp"] = datetime.utcfromtimestamp(int(request.data["timestamp"]))
            serializer = GpsSerializer(data=data)
            if serializer.is_valid():
                serializer.save(workspace=workspace, user=user)
                tmp = {}
                for item in serializer.data:
                    tmp[item] = serializer.data[item]
                if tmp["timestamp"]:
                    tmp["timestamp"] = int(parse(tmp["timestamp"]).replace(tzinfo=timezone.utc).timestamp())
                return JsonResponse(tmp, safe=False)
            return JsonResponse(serializer.errors, safe=False)
        except Exception as e:
            return JsonResponse(str(e), safe=False)
    def patch(self, request):
        try:
            id = request.query_params.get("id", None)
            user_id = request.data.get("user_id", None)
            workspace_id = request.data.get("workspace_id", None)
            if user_id:
                user = Users.objects.get(id=user_id)
            if workspace_id:
                workspace = Workspaces.objects.get(id=workspace_id)
            gps = Gps.objects.get(id=id)
            data = request.data.copy()
            if request.data.get("timestamp"):
                data["timestamp"] = datetime.utcfromtimestamp(int(request.data["timestamp"]))
            serializer = GpsSerializer(gps, data=data)
            if serializer.is_valid():
                if user_id and workspace_id:
                    serializer.save(user=user, workspace=workspace)
                elif user_id:
                    serializer.save(user=user)
                elif workspace_id:
                    serializer.save(workspace=workspace)
                tmp = {}
                for item in serializer.data:
                    tmp[item] = serializer.data[item]
                if tmp["timestamp"]:
                    tmp["timestamp"] = int(parse(tmp["timestamp"]).replace(tzinfo=timezone.utc).timestamp())
                return JsonResponse(tmp, safe=False)
            return JsonResponse(serializer.errors, safe=False)
        except Exception as e:
            return JsonResponse(str(e), safe=False)

class CurrentGpsView(APIView):
    '''
    Current Gps Class
    The purpose of this is to return users and their location and timestamp 
    '''
    def get(self, request):
        workspace_id = request.query_params.get("workspace_id", None)
        user_id = request.query_params.get("user_id", None)
        if user_id:
            q = Q()
            if workspace_id:
                q &= Q(workspace_id=workspace_id)
            q &= Q(user_id=user_id)
            current_gps = Gps.objects.filter(q).order_by('-timestamp')[:1]
            if current_gps:
                current_gps[0].timestamp = current_gps[0].timestamp.replace(tzinfo=timezone.utc).timestamp()
            serializer = GpsViewSerializer(current_gps, many=True)
            return JsonResponse(serializer.data, safe=False)
        else:
            result = []
            users = Users.objects.all()
            for i in range(len(users)):
                q = Q()
                if workspace_id:
                    q &= Q(workspace_id=workspace_id)
                q &= Q(user_id=users[i].pk)
                current_gps = Gps.objects.values().filter(q).order_by('-timestamp')[:1]
                if current_gps:
                    current_gps[0]["timestamp"] = current_gps[0]["timestamp"].replace(tzinfo=timezone.utc).timestamp()
                    serializer = GpsViewSerializer(current_gps, many=True)
                    result.append(serializer.data[0])
            return JsonResponse(result, safe=False)

class TimeSheet(APIView):
    '''
    TimeSheet class
    Nested JSON of the user > payroll time period > work_time period. 
    '''
    def get(self, request):
        q = Q()
        workspace_id = request.query_params.get("workspace_id", None)
        user_id = request.query_params.get("user_id", None)
        start_time = request.query_params.get("start_time", None)
        end_time = request.query_params.get("end_time", None)
        approved = request.query_params.get("approved", None)
        if (workspace_id):
            q &= Q(workspace_id=workspace_id)
        if (user_id):
            q &= Q(user_id=user_id)
        if (start_time):
            start_time = datetime.utcfromtimestamp(int(start_time))
            q &= Q(stop_time__gt=start_time)
        if (end_time):
            end_time = datetime.utcfromtimestamp(int(end_time))
            q &= Q(start_time__lt=end_time)
        if (approved):
            q &= Q(approved=approved)
        if end_time == None:
            end_time = parse(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        payroll = list(Payroll_time_period.objects.annotate(
            payroll_start_time=Case(
                When(start_time__lt=start_time, then=start_time),
                default=F("start_time"),
                output_field=DateTimeWithoutTZField()
            ),
            payroll_stop_time=Case(
                When(stop_time__gt=end_time, then=end_time),
                default=F("stop_time"),
                output_field=DateTimeWithoutTZField()
            )
        ).values("id", "workspace_id", "user_id", "start_time", "stop_time", "approved", "note", "payroll_start_time", "payroll_stop_time").annotate(
            duration=Epoch(F("payroll_stop_time")-F("payroll_start_time"))
        ).filter(q))
        for row in payroll:
            tmp = list(Work_time_period.objects.annotate(
                worktime_start_time=Case(
                    When(start_time__lt=row["payroll_start_time"], then=row["payroll_start_time"]),
                    default=F("start_time"),
                    output_field=DateTimeWithoutTZField()
                ),
                worktime_stop_time=Case(
                    When(stop_time__gt=row["payroll_stop_time"], then=row["payroll_stop_time"]),
                    default=F("stop_time"),
                    output_field=DateTimeWithoutTZField()
                )
            ).values("id", "worktime_start_time", "worktime_stop_time", "note", "timetype_id").annotate(
                duration=Epoch(F('worktime_stop_time')-F('worktime_start_time'))
            ).filter(
                workspace_id=row["workspace_id"],
                user_id=row["user_id"],
                stop_time__gt=row["payroll_start_time"],
                start_time__lt=row["payroll_stop_time"],
                approved=row["approved"]
            ))
            for i in range(len(tmp)):
                tmp[i]["worktime_start_time"] = int(tmp[i]["worktime_start_time"].replace(tzinfo=timezone.utc).timestamp())
                tmp[i]["worktime_stop_time"] = int(tmp[i]["worktime_stop_time"].replace(tzinfo=timezone.utc).timestamp())
            row.pop("payroll_start_time")
            row.pop("payroll_stop_time")
            row["start_time"] = int(row["start_time"].replace(tzinfo=timezone.utc).timestamp())
            row["stop_time"] = int(row["stop_time"].replace(tzinfo=timezone.utc).timestamp())
            row["work_time_period"] = tmp
        make_json(payroll, "time_sheet.json")
        return JsonResponse(payroll, safe=False)

class GpsPathView(APIView):
    '''
    GpsPath View Class
    - The purpose of this is to get a GPS path the user took based on data submitted with ~/api/gps during time logging. 
    - Ideally , passing WO ID or payroll_time_period ID’s would filter and return results. This would have to be accomplished by getting the time and users 
      on the WO, then filtering coordinate records by that. 
    '''
    # GET
    def get(self, request):
        q = Q()
        user_id = request.query_params.get('user_id', None)
        start_time = request.query_params.get('start_time', None)
        stop_time = request.query_params.get('stop_time', None)
        workspace_id = request.query_params.get('workspace_id', None)

        if user_id:
            q &= Q(user_id = user_id)
        if start_time:
            start_time = datetime.utcfromtimestamp(int(start_time))
            q &= Q(timestamp__gte = start_time)
        if stop_time:
            stop_time = datetime.utcfromtimestamp(int(stop_time))
            q &= Q(timestamp__lte = stop_time)
        if workspace_id:
            q &= Q(workspace_id = workspace_id)
        queryset = Gps.objects.filter(q)
        for row in queryset:
            row.timestamp = row.timestamp.replace(tzinfo=timezone.utc).timestamp()
        serializer = GpsViewSerializer(queryset, many=True)

        return JsonResponse(serializer.data, safe=False)

class PayrollReportView(APIView):
    '''
    Payroll Report View
    - This endpoint  shows time grouped by user and date
    - Responses need to be totaled and grouped by day
    '''
    # GET
    def get(self, request):
        q = Q()
        workspace_id = request.query_params.get("workspace_id", None)
        user_ids = request.query_params.get("user_ids", None)
        start_time = request.query_params.get("start_time", None)
        end_time = request.query_params.get("end_time", None)
        approved = request.query_params.get("approved", None)
        if start_time:
            start_time = datetime.utcfromtimestamp(int(start_time))
            q &= Q(stop_time__gt=start_time)
        if end_time:
            end_time = datetime.utcfromtimestamp(int(end_time))
            q &= Q(start_time__lt=end_time)
        if user_ids:
            q &= Q(user_id__in=user_ids)
        if workspace_id:
            q &= Q(workspace_id=workspace_id)
        if approved:
            q &= Q(approved=approved)
        if end_time == None:
            end_time = parse(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        payroll_time = Payroll_time_period.objects.filter(q)
        result = []
        for i in range(len(payroll_time)):
            if payroll_time[i].stop_time == None:
                payroll_time[i].stop_time = parse(datetime.now().strftime("%Y-%m-%d %H:%M"))
            if payroll_time[i].start_time < start_time:
                payroll_time[i].start_time = start_time
            if payroll_time[i].stop_time > end_time:
                payroll_time[i].stop_time = end_time
            worktime_period = Work_time_period.objects.annotate(
                worktime_start_time=Case(
                    When(start_time__lt=payroll_time[i].start_time, then=payroll_time[i].start_time),
                    default=F("start_time"),
                    output_field=DateTimeWithoutTZField()
                ),
                worktime_stop_time=Case(
                    When(stop_time__gt=payroll_time[i].stop_time, then=payroll_time[i].stop_time),
                    default=F("stop_time"),
                    output_field=DateTimeWithoutTZField()
                )
            ).values('start_time__date', 'user_id', 'timetype_id', 'workspace_id').annotate(
                payroll_duration=Sum(Epoch(F('worktime_stop_time')-F('worktime_start_time'))), start_gps=F("start_gps"), stop_gps=F("stop_gps")
            ).filter(
                start_time__lt=payroll_time[i].stop_time, 
                stop_time__gt=payroll_time[i].start_time, 
                workspace_id=payroll_time[i].workspace.id,
                user_id=payroll_time[i].user.id
            )
            worktime = []
            for j in range(len(worktime_period)):
                flag = 0
                for k in range(len(worktime)):
                    if worktime[k]["user_id"] == worktime_period[j]["user_id"] and worktime[k]["date"] == worktime_period[j]["start_time__date"]:
                        timetype_item = {}
                        flag = 1
                        timetype = TimeType.objects.get(id=worktime_period[j]["timetype_id"])
                        timetype_item["time_type_id"] = timetype.id
                        timetype_item["time_type"] = timetype.name
                        timetype_item["pay_type"] = timetype.pay_type
                        timetype_item["timetype_duration"] = worktime_period[j]["payroll_duration"]
                        if worktime_period[j]["start_gps"] and worktime_period[j]["stop_gps"]:
                            timetype_item["distance"] = distance(worktime_period[j]["start_gps"], worktime_period[j]["stop_gps"])
                        worktime[k]["TimeType" + str(timetype.id)] = timetype_item
                if flag == 0:
                    timetype_item = {}
                    timetype_item["user_id"] = worktime_period[j]["user_id"]
                    timetype_item["full_name"] = payroll_time[i].user.full_name
                    timetype_item["date"] = worktime_period[j]["start_time__date"]
                    timetype_item["payroll_duration"] = (payroll_time[i].stop_time - payroll_time[i].start_time).total_seconds()

                    timetype = TimeType.objects.get(id=worktime_period[j]["timetype_id"])
                    timetype_item["TimeType" + str(timetype.id)] = {}
                    timetype_item["TimeType" + str(timetype.id)]["time_type_id"] = timetype.id
                    timetype_item["TimeType" + str(timetype.id)]["time_type"] = timetype.name
                    timetype_item["TimeType" + str(timetype.id)]["pay_type"] = timetype.pay_type
                    timetype_item["TimeType" + str(timetype.id)]["timetype_duration"] = worktime_period[j]["payroll_duration"]
                    if worktime_period[j]["start_gps"] and worktime_period[j]["stop_gps"]:
                        timetype_item["TimeType" + str(timetype.id)]["distance"] = distance(worktime_period[j]["start_gps"], worktime_period[j]["stop_gps"])
                    worktime.append(timetype_item)
            if worktime:
                result.append(worktime)
        make_json(result, "payroll_report.json")
        return JsonResponse(result, safe=False)

class PayrollTimePeriodView(APIView):
    # add permission to check if user is authenticated
    # permission_classes = [permissions.IsAuthenticated]
    '''
    PayrollTimePeriod Class View
    - This will be POSTed with start time and gps, without stop time and stop GPS until the user ends the clock. Response needs to include PK of payroll_time_period. 
    '''
    def get(self, request):
        q = Q()
        user_id = request.query_params.get('user_id', None)
        if user_id:
            q &= Q(user_id=user_id)
        workspace_id = request.query_params.get('workspace_id', None)
        if workspace_id:
            q &= Q(workspace_id=workspace_id)
        start_time = request.query_params.get('start_time', None)
        if start_time:
            start_time = datetime.utcfromtimestamp(int(start_time))
            q &= Q(start_time__gte=start_time)
        stop_time = request.query_params.get('stop_time', None)
        if stop_time:
            stop_time = datetime.utcfromtimestamp(int(stop_time))
            q &= Q(stop_time__lte=stop_time)
        payrolls = Payroll_time_period.objects.filter(q)
        for row in payrolls:
            row.start_time = row.start_time.replace(tzinfo=timezone.utc).timestamp() 
            if row.stop_time:
                row.stop_time = row.stop_time.replace(tzinfo=timezone.utc).timestamp()
        serializer = PayrollTimePeriodViewSerializer(payrolls, many=True)
        return JsonResponse(serializer.data, safe=False)

    # POST
    # PK
    def post(self, request):
        try:
            workspace_id = request.data.get('workspace_id', None)
            user_id = request.data.get('user_id', None)
            workspace = Workspaces.objects.get(id=workspace_id)
            user = Users.objects.get(id=user_id)
            data = request.data.copy()
            if request.data.get("start_time"):
                data["start_time"] = datetime.utcfromtimestamp(int(request.data["start_time"]))
            if request.data.get("stop_time"):
                data["stop_time"] = datetime.utcfromtimestamp(int(request.data["stop_time"]))
            serializer = PayrollTimePeriodSerializer(data=data)
            if serializer.is_valid():
                serializer.save(workspace=workspace, user=user)
                tmp = {}
                for item in serializer.data:
                    tmp[item] = serializer.data[item]
                if tmp["start_time"]:
                    tmp["start_time"] = int(parse(tmp["start_time"]).replace(tzinfo=timezone.utc).timestamp())
                if tmp["stop_time"]:
                    tmp["stop_time"] = int(parse(tmp["stop_time"]).replace(tzinfo=timezone.utc).timestamp())
                return JsonResponse(tmp, safe=False)
            return JsonResponse(serializer.errors, safe=False)
        except Exception as e:
            return JsonResponse(str(e), safe=False)
    # Patch
    # PK
    def patch(self, request):
        try:
            id = request.query_params.get('id', None)
            user_id = request.data.get('user_id', None)
            payroll = Payroll_time_period.objects.get(id=id)
            workspace_id = request.data.get('workspace_id', None)
            stop_gps = request.data.get('stop_gps', None)
            start_gps = request.data.get('start_gps', None)    
            workspace = Workspaces.objects.get(id=workspace_id)
            user = Users.objects.get(id=user_id)
            if stop_gps == None:
                payroll.stop_gps = None
            if start_gps == None:
                payroll.start_gps = None
            data = request.data.copy()
            if request.data.get("start_time"):
                data["start_time"] = datetime.utcfromtimestamp(int(request.data["start_time"]))
            if request.data.get("stop_time"):
                data["stop_time"] = datetime.utcfromtimestamp(int(request.data["stop_time"]))
            serializer = PayrollTimePeriodSerializer(payroll, data=data)
            if serializer.is_valid():
                serializer.save(workspace=workspace,user=user)
                tmp = {}
                for item in serializer.data:
                    tmp[item] = serializer.data[item]
                if tmp["start_time"]:
                    tmp["start_time"] = int(parse(tmp["start_time"]).replace(tzinfo=timezone.utc).timestamp())
                if tmp["stop_time"]:
                    tmp["stop_time"] = int(parse(tmp["stop_time"]).replace(tzinfo=timezone.utc).timestamp())
                return JsonResponse(tmp, safe=False)
            return JsonResponse(serializer.errors, safe=False)
        except Exception as e:
            return JsonResponse(str(e), safe=False)

class CrewView(APIView):
    '''
    Crew View Class
    - This is for the purpose of logging time for multiple users at once (crew of 2-4 people in a truck). The front end will GET 
      /api/crew to know the users to log time for.
    '''
    #GET
    def get(self, request):
        q = Q()
        workspace_id = request.query_params.get('workspace_id', None)
        if workspace_id is not None:
            q &= Q(workspace_id=workspace_id)
        isActive = request.query_params.get('isActive', None)
        if isActive is not None:
            q &= Q(active=isActive)       
        foreman_user_id = request.query_params.get('foreman_user_id', None)
        if foreman_user_id is not None:
            q &= Q(foreman_user_id=foreman_user_id)
        crews = Crew.objects.filter(q)
        serializer = CrewSerializer(crews, many=True)
        return JsonResponse(serializer.data, safe=False)
    #POST
    def post(self, request):
        try:
            workspace_id = request.data.get("workspace_id", None)
            workspace = Workspaces.objects.get(id=workspace_id)
            serializer = CrewSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(workspace=workspace)
                return JsonResponse(serializer.data, safe=False)
            return JsonResponse(serializer.errors, safe=False)
        except Exception as e:
            return JsonResponse(str(e), safe=False)
    #PATCH
    def patch(self, request):
        try:
            id = request.query_params.get('id', None)
            crew = Crew.objects.get(id=id)
            workspace_id = request.data.get('workspace_id', None)    
            workspace = Workspaces.objects.get(id=workspace_id)
            serializer = CrewSerializer(crew, data=request.data)
            if serializer.is_valid():
                serializer.save(workspace=workspace)
                return JsonResponse(serializer.data, safe=False)        
            return JsonResponse(serializer.errors, safe=False)
        except Exception as e:
            return JsonResponse(str(e), safe=False)

class WorkTimePeriodView(APIView):
    '''
    WorkTImePeriodView Class
     - This endpoint can return multiple nested time periods
    '''
    #GET
    def get(self, request):
        q = Q()
        workspace_id = request.query_params.get("workspace_id", None)
        if workspace_id:
            q &= Q(workspace_id=workspace_id)
        user_id = request.query_params.get("user_id", None)
        if user_id:
            q &= Q(user_id=user_id)
        work_id = request.query_params.get("work_id", None)
        if work_id:
            q &= Q(work_id=work_id)
        start_time = request.query_params.get('start_time', None)
        if start_time:
            start_time = datetime.utcfromtimestamp(int(start_time))
            q &= Q(start_time__gte=start_time)
        stop_time = request.query_params.get('stop_time', None)
        if stop_time:
            stop_time = datetime.utcfromtimestamp(int(stop_time))
            q &= Q(stop_time__lte=stop_time)       
        workrolls = Work_time_period.objects.filter(q)
        for row in workrolls:
            row.start_time = row.start_time.replace(tzinfo=timezone.utc).timestamp() 
            if row.stop_time:
                row.stop_time = row.stop_time.replace(tzinfo=timezone.utc).timestamp()
        serializer = PayrollTimePeriodViewSerializer(workrolls, many=True)
        return JsonResponse(serializer.data, safe=False)
    #POST
    def post(self, request):
        try:
            workspace_id = request.data.get("workspace_id", None)
            timetype_id = request.data.get("timetype_id", None)
            user_id = request.data.get("user_id", None)
            workspace = Workspaces.objects.get(id=workspace_id)
            timetype = TimeType.objects.get(id=timetype_id)
            user = Users.objects.get(id=user_id)
            data = request.data.copy()
            if request.data.get("start_time"):
                data["start_time"] = datetime.utcfromtimestamp(int(request.data["start_time"]))
            if request.data.get("stop_time"):
                data["stop_time"] = datetime.utcfromtimestamp(int(request.data["stop_time"]))
            serializer = WorkTimePeriodSerializer(data=data)
            if serializer.is_valid():
                serializer.save(workspace=workspace, timetype=timetype, user=user)
                tmp = {}
                for item in serializer.data:
                    tmp[item] = serializer.data[item]
                if tmp["start_time"]:
                    tmp["start_time"] = int(parse(tmp["start_time"]).replace(tzinfo=timezone.utc).timestamp())
                if tmp["stop_time"]:
                    tmp["stop_time"] = int(parse(tmp["stop_time"]).replace(tzinfo=timezone.utc).timestamp())
                return JsonResponse(tmp, safe=False)
            return JsonResponse(serializer.errors, safe=False)
        except Exception as e:
            return JsonResponse(str(e), safe=False)
    #PATCH
    def patch(self, request):
        try:
            id = request.query_params.get('id', None)
            timetype_id = request.data.get("timetype_id", None)
            user_id = request.data.get("user_id", None)
            workspace_id = request.data.get('workspace_id', None) 
            stop_gps = request.data.get('stop_gps', None)
            start_gps = request.data.get('start_gps', None)
            worktime = Work_time_period.objects.get(id=id)
            workspace = Workspaces.objects.get(id=workspace_id)
            timetype = TimeType.objects.get(id=timetype_id)
            user = Users.objects.get(id=user_id)
            if stop_gps == None:
                worktime.stop_gps = None
            if start_gps == None:
                worktime.start_gps = None
            data = request.data.copy()
            if request.data.get("start_time"):
                data["start_time"] = datetime.utcfromtimestamp(int(request.data["start_time"]))
            if request.data.get("stop_time"):
                data["stop_time"] = datetime.utcfromtimestamp(int(request.data["stop_time"]))
            serializer = WorkTimePeriodSerializer(worktime, data=data)
            if serializer.is_valid():
                serializer.save(workspace=workspace, timetype=timetype, user=user)
                tmp = {}
                for item in serializer.data:
                    tmp[item] = serializer.data[item]
                if tmp["start_time"]:
                    tmp["start_time"] = int(parse(tmp["start_time"]).replace(tzinfo=timezone.utc).timestamp())
                if tmp["stop_time"]:
                    tmp["stop_time"] = int(parse(tmp["stop_time"]).replace(tzinfo=timezone.utc).timestamp())
                return JsonResponse(tmp, safe=False)
            
            return JsonResponse(serializer.errors, safe=False)
        except Exception as e:
            return JsonResponse(str(e), safe=False)

class WorkReportView(APIView):
    '''
    WorkReportView Class
    This endpoint  shows time grouped by user, date, and work order
    '''
    # GET
    def get(self, request):
        q = Q()
        workspace_id = request.query_params.get("workspace_id", None)
        user_ids = request.query_params.get("user_ids", None)
        start_time = request.query_params.get("start_time", None)
        end_time = request.query_params.get("end_time", None)
        approved = request.query_params.get("approved", None)
        if start_time:
            start_time = datetime.utcfromtimestamp(int(start_time))
            q &= Q(stop_time__gt=start_time)
        if end_time:
            end_time = datetime.utcfromtimestamp(int(end_time))
            q &= Q(start_time__lt=end_time)
        if user_ids:
            q &= Q(user_id__in=user_ids)
        if workspace_id:
            q &= Q(workspace_id=workspace_id)
        if (approved):
            q &= Q(approved=approved)
        if end_time == None:
            end_time = parse(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        work_time = Work_time_period.objects.annotate(
            worktime_start_time=Case(
                When(start_time__lt=start_time, then=start_time),
                default=F("start_time"),
                output_field=DateTimeWithoutTZField()
            ),
            worktime_stop_time=Case(
                When(stop_time__gt=end_time, then=end_time),
                default=F("stop_time"),
                output_field=DateTimeWithoutTZField()
            )
        ).values('start_time__date', 'user_id', 'timetype_id', 'work_id').annotate(
            payroll_duration=Sum(Epoch(F('worktime_stop_time')-F('worktime_start_time'))), start_gps=F("start_gps"), stop_gps=F("stop_gps")
        ).filter(q)
        result = []
        for j in range(len(work_time)):
            flag = 0
            user = Users.objects.get(id=work_time[j]["user_id"])
            for k in range(len(result)):
                if result[k]["user_id"] == user.id and result[k]["date"] == work_time[j]["start_time__date"] and result[k]["work_id"] == work_time[j]["work_id"]:
                    flag = 1
                    timetype = TimeType.objects.get(id=work_time[j]["timetype_id"])
                    result[k]["TimeType" + str(timetype.id)] = {}
                    result[k]["TimeType" + str(timetype.id)]["time_type_id"] = timetype.id
                    result[k]["TimeType" + str(timetype.id)]["time_type"] = timetype.name
                    result[k]["TimeType" + str(timetype.id)]["pay_type"] = timetype.pay_type
                    result[k]["TimeType" + str(timetype.id)]["payroll_duration"] = work_time[j]["payroll_duration"]
                    if work_time[j]["start_gps"] and work_time[j]["stop_gps"]:
                        result[k]["TimeType" + str(timetype.id)]["distance"] = distance(work_time[j]["start_gps"], work_time[j]["stop_gps"])
            if flag == 0:
                tmp = {}
                tmp["user_id"] = user.id
                tmp["full_name"] = user.full_name
                tmp["date"] = work_time[j]["start_time__date"]
                tmp["work_id"] = work_time[j]["work_id"]
                timetype = TimeType.objects.get(id=work_time[j]["timetype_id"])
                tmp["TimeType" + str(timetype.id)] = {}
                tmp["TimeType" + str(timetype.id)]["time_type_id"] = timetype.id
                tmp["TimeType" + str(timetype.id)]["time_type"] = timetype.name
                tmp["TimeType" + str(timetype.id)]["pay_type"] = timetype.pay_type
                tmp["TimeType" + str(timetype.id)]["payroll_duration"] = work_time[j]["payroll_duration"]
                if work_time[j]["start_gps"] and work_time[j]["stop_gps"]:
                    tmp["TimeType" + str(timetype.id)]["distance"] = distance(work_time[j]["start_gps"], work_time[j]["stop_gps"])
                result.append(tmp)
        make_json(result, "work_report.json")
        return JsonResponse(result, safe=False)

class TimeUtilizationView(APIView):
    '''
    TimeUtilizationView Class
    This is to calculate the efficiency of techs. The endpoint will return all time times and the percentage of that time relative to payroll time. 
    If they log 8 hours for payroll time and work 4 hours and travel 1 hour, the response would look like: 
        - Travel: .125
        - Work:  .5
        - Unlogged: .375
    '''
    # GET
    def time_utilization(self, user_id, workspace_id, payroll_start_time, payroll_stop_time, payroll_duration):
        if payroll_stop_time == None:
            payroll_stop_time = parse(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        data = Work_time_period.objects.annotate(
            worktime_start_time=Case(
                When(start_time__lt=payroll_start_time, then=payroll_start_time),
                default=F('start_time'),
                output_field=DateTimeWithoutTZField()
            ),
            worktime_stop_time=Case(
                When(stop_time__gt=payroll_stop_time, then=payroll_stop_time),
                default=F("stop_time"),
                output_field=DateTimeWithoutTZField()
            )
        ).values("timetype_id").annotate(
            duration=Sum(Round(Epoch(F("worktime_stop_time")-F("worktime_start_time")) / payroll_duration, 2))
        ).filter(user_id=user_id, workspace_id=workspace_id, stop_time__gt=payroll_start_time, start_time__lt=payroll_stop_time)
        return data
    def get(self, request):
        q = Q()
        workspace_id = request.query_params.get("workspace_id", None)
        start_time = request.query_params.get("start_time", None)
        stop_time = request.query_params.get("stop_time", None)
        if start_time:
            start_time = datetime.utcfromtimestamp(int(start_time))
            q &= Q(stop_time__gt=start_time)
        if stop_time:
            stop_time = datetime.utcfromtimestamp(int(stop_time))
            q &= Q(start_time__lt=stop_time)
        if workspace_id:
            q &= Q(workspace_id=workspace_id)
        if stop_time == None:
            stop_time = parse(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        payroll_data = Payroll_time_period.objects.filter(q)
        result = [{} for i in range(len(payroll_data))]
        for i in range(len(payroll_data)):
            if (payroll_data[i].start_time < start_time):
                payroll_data[i].start_time = start_time
            if (payroll_data[i].stop_time > stop_time):
                payroll_data[i].stop_time = stop_time
            payroll_duration = (payroll_data[i].stop_time - payroll_data[i].start_time).total_seconds()
            tmp = self.time_utilization(payroll_data[i].user.id, payroll_data[i].workspace.id, payroll_data[i].start_time, payroll_data[i].stop_time, payroll_duration)
            for j in range(len(tmp)):
                result[i]["user"] = payroll_data[i].user.full_name
                timetype = TimeType.objects.get(id=tmp[j]["timetype_id"])
                result[i][timetype.name] = tmp[j]["duration"]
        make_json(result, "time_utilization.json")
        return JsonResponse(result, safe=False)

class ActiveTimeView(APIView):  
    '''
    ActiveTimeView Class
    - This will be used  to show a map of everyone currently working with  a popup showing what they are working on.
    - Return a list of all users actively working. Work_time is more detailed than payroll_time so if a user has an active timer for work_time, 
      return that info. If no active work_time, return payroll_time (if active). 
    '''
    def get_active_time_worktime(self, params):
        queryset = Work_time_period.objects.filter(params)
        serializer = ActiveTimeWorkTimeSerializer(queryset, many=True)
        return serializer.data
    
    def get_active_time_payroll(self, params):
        queryset = Payroll_time_period.objects.filter(params)
        serializer = ActiveTimeWorkPayrollSerializer(queryset, many=True)
        return serializer.data
    #GET
    def get(self, request):
        try:
            q = Q()
            workspace_id = request.query_params.get('workspace_id', None)
            user_id = request.query_params.get('user_id', None)
            start_time = request.query_params.get('start_time', None)
            if workspace_id:
                q &= Q(workspace_id=workspace_id)            
            if user_id:
                q &= Q(user_id=user_id)
            if start_time:
                start_time = datetime.utcfromtimestamp(int(start_time))
                q &= Q(start_time__gte=start_time)
            q &= Q(stop_time=None)
            data = self.get_active_time_worktime(q)
            data1 = self.get_active_time_payroll(q)
            tmp = []
            for i in range(len(data)):
                for j in range(len(data)):
                    if i != j and data[i]["user_id"] == data[j]["user_id"]:
                        if data[i]["log_time"] < data[j]["log_time"]:
                            if tmp.count(i) == 0:
                                tmp.append(i)
                        else:
                            if tmp.count(j) == 0:
                                tmp.append(j)
            tmp.sort(reverse=True)
            for i in tmp:
                data.pop(i)
            for item in data1:
                flag = 0
                for i in range(len(data)):
                    if data[i]["user_id"] == item["user_id"]:
                        flag = 1
                        if data[i]["log_time"] < item["log_time"]:
                            data.pop(i)
                            item["log_time"] = item["log_time"]
                            data.append(item)
                if flag == 0:
                    data.append(item)
            for row in data:
                tmp = parse(row["log_time"])
                row["log_time"] = int(tmp.replace(tzinfo=timezone.utc).timestamp())
            make_json(data, "active_time.json")
            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse(str(e), safe=False)

class UsersView(APIView):
    '''
    Users view class
    This class is used to manage users
    '''
    def get(self, request):
        q = Q()
        full_name = request.query_params.get("full_name", None)
        email = request.query_params.get("email", None)
        user_name = request.query_params.get("user_name", None)
        admin = request.query_params.get("admin", None)
        if full_name:
            q &= Q(full_name=full_name)
        if email:
            q &= Q(email=email)
        if user_name:
            q &= Q(user_name=user_name)
        if (admin):
            q &= Q(admin=admin)
        user = Users.objects.filter(q)
        serializer = UsersSerializer(user, many=True)
        return JsonResponse(serializer.data, safe=False)
    def post(self, request):
        serializer = UsersSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, safe=False)
        return JsonResponse(serializer.errors, safe=False)
    def patch(self, request):
        try:
            id = request.query_params.get("id", None)
            user = Users.objects.get(id=id)
            serializer = UsersSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(serializer.data, safe=False)
            return JsonResponse(serializer.errors, safe=False)
        except Exception as e:
            return JsonResponse(str(e), safe=False)

class ReportCSV(APIView):
    def get(self, request, name):
        excel_dest = 'downloads/report_api_excel/'
        isExist = os.path.exists(excel_dest)
        if not isExist:
            os.makedirs(excel_dest)
        files = glob.glob('downloads/report_api_json/*', recursive=True)
        for single_file in files:
            with open(single_file, 'r') as f:
                try:
                    if f.name.find(name) != -1:
                        file_name = f.name[26:-5]
                        workbook = Workbook(f.name)
                        workbook.save(excel_dest + file_name + ".csv", SaveFormat.CSV)
                        response = download_excel(request, excel_dest + file_name + ".csv", file_name, type="csv")
                        return response
                except KeyError:
                    print(f'Skipping {single_file}')
        return JsonResponse("Not Found", safe=False)
        
class ReportXlsx(APIView):
    def get(self, request, name):
        excel_dest = 'downloads/report_api_excel/'
        isExist = os.path.exists(excel_dest)
        if not isExist:
            os.makedirs(excel_dest)
        files = glob.glob('downloads/report_api_json/*', recursive=True)
        for single_file in files:
            with open(single_file, 'r') as f:
                try:
                    if f.name.find(name) != -1:
                        file_name = f.name[26:-5]
                        workbook = Workbook(f.name)
                        workbook.save(excel_dest + file_name + ".xlsx")
                        response = download_excel(request, excel_dest + file_name + ".xlsx", file_name, type="xlsx")
                        return response
                except KeyError:
                    print(f'Skipping {single_file}')
        return JsonResponse("Not Found", safe=False)