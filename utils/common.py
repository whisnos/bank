import json
from django.core import serializers
from django.db import models
from django.db.models.query import QuerySet
from datetime import datetime,date
import  decimal
class JsonCustomEncoder(json.JSONEncoder):
    def default(self, value):
        if isinstance(value,QuerySet):
            return list(value)
        if isinstance(value,models.Model):
            return json.loads(serializers.serialize('json',[value])[1:-1])
        if isinstance(value,dict):
            return json.loads(serializers.serialize('json',[value]))
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, date):
            return value.strftime('%Y-%m-%d')
        elif isinstance(value,decimal.Decimal):
            return float(value)
        else:
            return json.JSONEncoder.default(self, value)