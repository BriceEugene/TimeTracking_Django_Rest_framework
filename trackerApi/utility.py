from django.db.models import Func, IntegerField
import haversine as hs        # calculate distance between two gps points
from haversine import Unit    # distance unit
import os
from django.http import FileResponse
import json

class Epoch(Func):
    template = 'EXTRACT(epoch FROM %(expressions)s)'
    output_field = IntegerField()

def distance(loc1, loc2):
     data = hs.haversine(loc1,loc2, unit=Unit.MILES)
     return data

def download_excel(request, file, file_name):
    path_to_file = os.path.realpath(file)
    response = FileResponse(open(path_to_file, 'rb'))
    response['Content-Disposition'] = 'inline; filename=' + file_name + ".xlsx"
    return response

def make_json(data, file_name):
    path = "downloads/report_api_json/"
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)
    json_object = json.dumps(data, indent=4, default=str)
    with open(path + file_name, "w") as outfile:
        outfile.write(json_object)