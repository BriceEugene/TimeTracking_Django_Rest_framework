from django.db.models import Func, IntegerField
import haversine as hs        # calculate distance between two gps points
from haversine import Unit    # distance unit

class Epoch(Func):
    template = 'EXTRACT(epoch FROM %(expressions)s)'
    output_field = IntegerField()

def distance(loc1, loc2):
     data = hs.haversine(loc1,loc2, unit=Unit.MILES)
     return data