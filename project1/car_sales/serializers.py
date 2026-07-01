from rest_framework import serializers
from .models import *
from django.db import connections

class employeesalesserializers:
    DB_NAME = 'default'

    @staticmethod
    def fetch(dt_from, dt_to):
        query = """
        SELECT
            CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
            CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name,
            ii.make_name AS brand_name,
            vi.vehicle_model AS vehicle_name, 
            si.selling_date, 
            vi.mmr,
            si.selling_price
        FROM selling_info si
        INNER JOIN employee e ON si.employee_id = e.employee_id
        INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        WHERE si.selling_date BETWEEN %s AND %s;
        """
        with connections[employeesalesserializers.DB_NAME].cursor() as cursor:
            cursor.execute(query, [dt_from, dt_to])
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]


class storesalesserializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(dt_from, dt_to):
        query = """
        SELECT
            s.store_name,
            CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name,
            ii.make_name AS brand_name,
            vi.vehicle_model AS vehicle_name, 
            si.selling_date, 
            vi.mmr,
            si.selling_price
        FROM selling_info si
        INNER JOIN store s ON si.store_id = s.store_id
        INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        WHERE si.selling_date BETWEEN %s AND %s;
        """
        with connections[storesalesserializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [dt_from, dt_to])
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
