from django.db import models


"""
Epoch function
Usage: posts.annotate(response_time_sec=Epoch(F('end_date') - F('start_date')))
"""
class Epoch(django.db.models.expressions.Func):
    template = 'EXTRACT(epoch FROM %(expressions)s)::INTEGER'
    output_field = models.IntegerField()