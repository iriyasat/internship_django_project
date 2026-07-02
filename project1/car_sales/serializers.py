from rest_framework import serializers
from .models import *
from django.db import connections

class employeesalesserializers:
    DB_NAME = 'default'

    @staticmethod
    def fetch(dt_from, dt_to, store_id=None, employee_id=None):
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
        WHERE si.selling_date BETWEEN %s AND %s
        """
        params = [dt_from, dt_to]
        if store_id is not None:
            query += " AND si.store_id = %s"
            params.append(store_id)
        if employee_id is not None:
            query += " AND si.employee_id = %s"
            params.append(employee_id)

        with connections[employeesalesserializers.DB_NAME].cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]


class storesalesserializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(dt_from, dt_to, store_id=None, employee_id=None):
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
        WHERE si.selling_date BETWEEN %s AND %s
        """
        params = [dt_from, dt_to]
        if store_id is not None:
            query += " AND si.store_id = %s"
            params.append(store_id)
        if employee_id is not None:
            query += " AND si.employee_id = %s"
            params.append(employee_id)

        with connections[storesalesserializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]


class storevehiclesalesserializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(dt_from, dt_to, store_id=None, employee_id=None):
        query = """
        SELECT
            s.store_name,
            CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
            CONCAT(ii.make_name, ' ', vi.vehicle_model) AS vehicle_info,
            COUNT(si.sell_id) AS quantity_sold,
            vi.mmr AS mmr,
            SUM(si.selling_price) AS total_selling_price
        FROM selling_info si
        INNER JOIN store s ON si.store_id = s.store_id
        INNER JOIN employee e ON si.employee_id = e.employee_id
        INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        WHERE si.selling_date BETWEEN %s AND %s
        """
        params = [dt_from, dt_to]
        
        if store_id is not None:
            query += " AND si.store_id = %s"
            params.append(store_id)
        if employee_id is not None:
            query += " AND si.employee_id = %s"
            params.append(employee_id)
            
        query += """
        GROUP BY s.store_id, e.employee_id, vi.id, ii.make_id, vi.mmr
        ORDER BY total_selling_price DESC;
        """
        with connections[storevehiclesalesserializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
