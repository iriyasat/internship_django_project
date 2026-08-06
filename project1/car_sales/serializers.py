import datetime
import random
from rest_framework import serializers
from .models import *
from django.db import connections
from django.db import transaction


# ─── Query Helper Operations ───

def format_date_fields(item):
    """Utility to format date and datetime fields to string format in-place."""
    for key, val in item.items():
        if val and hasattr(val, 'strftime') and not isinstance(val, str):
            if key in ('created_at', 'updated_at'):
                item[key] = val.strftime('%Y-%m-%d %H:%M')
            elif key in ('selling_date', 'invoice_date', 'due_date', 'date_of_joining'):
                item[key] = val.strftime('%Y-%m-%d')
    return item

def execute_raw_fetch_all(db_name, query, params=None):
    with connections[db_name].cursor() as cursor:
        cursor.execute(query, params or [])
        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
    return [format_date_fields(dict(zip(columns, row))) for row in rows]

def execute_fetchone_query(db_name, query, params=None):
    with connections[db_name].cursor() as cursor:
        cursor.execute(query, params or [])
        row = cursor.fetchone()
        if row:
            columns = [col[0] for col in cursor.description]
            return format_date_fields(dict(zip(columns, row)))
    return None

def execute_cud_query(db_name, query, params=None):
    with connections[db_name].cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.lastrowid

def format_employee_filter(field_name, employee_id, params):
    if employee_id is None:
        return ""
    if isinstance(employee_id, (list, tuple, set)):
        if len(employee_id) == 1:
            params.append(list(employee_id)[0])
            return f" AND {field_name} = %s"
        elif len(employee_id) > 1:
            placeholders = ", ".join(["%s"] * len(employee_id))
            params.extend(employee_id)
            return f" AND {field_name} IN ({placeholders})"
        else:
            return " AND 1=0"
    else:
        params.append(employee_id)
        return f" AND {field_name} = %s"

def add_employee_clause(where_clauses, params, field_name, employee_id):
    if employee_id is None:
        return
    if isinstance(employee_id, (list, tuple, set)):
        if len(employee_id) == 1:
            where_clauses.append(f"{field_name} = %s")
            params.append(list(employee_id)[0])
        elif len(employee_id) > 1:
            placeholders = ", ".join(["%s"] * len(employee_id))
            where_clauses.append(f"{field_name} IN ({placeholders})")
            params.extend(employee_id)
        else:
            where_clauses.append("1=0")
    else:
        where_clauses.append(f"{field_name} = %s")
        params.append(employee_id)

def format_store_filter(field_name, store_id, params):
    if store_id is None:
        return ""
    if isinstance(store_id, (list, tuple, set)):
        if len(store_id) == 1:
            params.append(list(store_id)[0])
            return f" AND {field_name} = %s"
        elif len(store_id) > 1:
            placeholders = ", ".join(["%s"] * len(store_id))
            params.extend(store_id)
            return f" AND {field_name} IN ({placeholders})"
        else:
            return " AND 1=0"
    else:
        params.append(store_id)
        return f" AND {field_name} = %s"

def add_store_clause(where_clauses, params, field_name, store_id):
    if store_id is None:
        return
    if isinstance(store_id, (list, tuple, set)):
        if len(store_id) == 1:
            where_clauses.append(f"{field_name} = %s")
            params.append(list(store_id)[0])
        elif len(store_id) > 1:
            placeholders = ", ".join(["%s"] * len(store_id))
            where_clauses.append(f"{field_name} IN ({placeholders})")
            params.extend(store_id)
        else:
            where_clauses.append("1=0")
    else:
        where_clauses.append(f"{field_name} = %s")
        params.append(store_id)

def execute_raw_sql_query(db_name, select_base, count_base, table_alias, field_map, search_fields, limit, offset, search, store_id, employee_id, store_col, employee_col, filters):
    query = select_base
    count_query = count_base
    where_clauses = []
    params = []
    
    if store_id is not None and store_col:
        add_store_clause(where_clauses, params, store_col, store_id)
    if employee_id is not None and employee_col:
        if isinstance(employee_id, (list, tuple, set)):
            if len(employee_id) == 1:
                where_clauses.append(f"{employee_col} = %s")
                params.append(list(employee_id)[0])
            elif len(employee_id) > 1:
                placeholders = ", ".join(["%s"] * len(employee_id))
                where_clauses.append(f"{employee_col} IN ({placeholders})")
                params.extend(employee_id)
            else:
                where_clauses.append("1=0")
        else:
            where_clauses.append(f"{employee_col} = %s")
            params.append(employee_id)
        
    for key, val in filters.items():
        if val is not None and val != '':
            col_name = field_map.get(key, key)
            if '.' not in col_name and table_alias:
                col_name = f"{table_alias}.{col_name}"
            where_clauses.append(f"{col_name} = %s")
            params.append(val)
            
    if search and search_fields:
        search_clauses = []
        search_param = f"%{search}%"
        for field in search_fields:
            col_name = field_map.get(field, field)
            if '.' not in col_name and table_alias:
                col_name = f"{table_alias}.{col_name}"
            search_clauses.append(f"{col_name} LIKE %s")
            params.append(search_param)
        where_clauses.append("(" + " OR ".join(search_clauses) + ")")
        
    where_str = ""
    if where_clauses:
        where_str = " AND " + " AND ".join(where_clauses)
        
    query = query.replace("WHERE 1=1", f"WHERE 1=1{where_str}")
    count_query = count_query.replace("WHERE 1=1", f"WHERE 1=1{where_str}")
    
    with connections[db_name].cursor() as cursor:
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
    limit_clause = ""
    query_params = list(params)
    if limit is not None and limit >= 0:
        limit_clause = "LIMIT %s OFFSET %s"
        query_params.extend([limit, offset])
        
    query += f" {limit_clause}"
    
    with connections[db_name].cursor() as cursor:
        cursor.execute(query, query_params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        
    data = [format_date_fields(dict(zip(columns, row))) for row in rows]
    return total, data

# ─── Serializer Implementations ───

class employeesalesserializers:
    DB_NAME = 'default'
    @staticmethod
    def fetch(dt_from, dt_to, store_id=None, employee_id=None):
        query = """
        SELECT CONCAT(e.first_name, ' ', e.last_name) AS employee_name, CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name,
               ii.make_name AS brand_name, vi.vehicle_model AS vehicle_name, si.selling_date, vi.mmr, si.selling_price
        FROM selling_info si
        INNER JOIN employee e ON si.employee_id = e.employee_id
        INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        WHERE si.selling_date BETWEEN %s AND %s
        """
        params = [dt_from, dt_to]
        query += format_store_filter("si.store_id", store_id, params)
        query += format_employee_filter("si.employee_id", employee_id, params)
        return execute_raw_fetch_all(employeesalesserializers.DB_NAME, query, params)

class storesalesserializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(dt_from, dt_to, store_id=None, employee_id=None):
        query = """
        SELECT s.store_name, CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name,
               ii.make_name AS brand_name, vi.vehicle_model AS vehicle_name, si.selling_date, vi.mmr, si.selling_price
        FROM selling_info si
        INNER JOIN store s ON si.store_id = s.store_id
        INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        WHERE si.selling_date BETWEEN %s AND %s
        """
        params = [dt_from, dt_to]
        query += format_store_filter("si.store_id", store_id, params)
        query += format_employee_filter("si.employee_id", employee_id, params)
        return execute_raw_fetch_all(storesalesserializer.DB_NAME, query, params)

class storevehiclesalesserializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(dt_from, dt_to, store_id=None, employee_id=None):
        query = """
        SELECT s.store_name, CONCAT(e.first_name, ' ', e.last_name) AS employee_name, CONCAT(ii.make_name, ' ', vi.vehicle_model) AS vehicle_info,
               COUNT(si.sell_id) AS quantity_sold, vi.mmr AS mmr, SUM(si.selling_price) AS total_selling_price
        FROM selling_info si
        INNER JOIN store s ON si.store_id = s.store_id
        INNER JOIN employee e ON si.employee_id = e.employee_id
        INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        WHERE si.selling_date BETWEEN %s AND %s
        """
        params = [dt_from, dt_to]
        query += format_store_filter("si.store_id", store_id, params)
        query += format_employee_filter("si.employee_id", employee_id, params)
        query += " GROUP BY s.store_id, e.employee_id, vi.id, ii.make_id, vi.mmr ORDER BY total_selling_price DESC"
        return execute_raw_fetch_all(storevehiclesalesserializer.DB_NAME, query, params)

class customervehiclesalesserializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(dt_from, dt_to, store_id=None, employee_id=None):
        query = """
        SELECT CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name, CONCAT(ii.make_name, ' ', vi.vehicle_model) AS vehicle_info,
               s.store_name, vi.mmr, si.selling_price, (si.selling_price - vi.mmr) AS mmr_vs_selling_price, si.selling_date
        FROM selling_info si
        INNER JOIN store s ON si.store_id = s.store_id
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        WHERE si.selling_date BETWEEN %s AND %s
        """
        params = [dt_from, dt_to]
        query += format_store_filter("si.store_id", store_id, params)
        query += format_employee_filter("si.employee_id", employee_id, params)
        query += " ORDER BY si.selling_date DESC"
        return execute_raw_fetch_all(customervehiclesalesserializer.DB_NAME, query, params)

class customerstorespendingserializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(dt_from, dt_to, store_id=None, employee_id=None):
        query = """
        SELECT CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name, s.store_name, SUM(si.selling_price) AS total_spent, COUNT(si.sell_id) AS total_purchased
        FROM selling_info si
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN store s ON si.store_id = s.store_id
        WHERE si.selling_date BETWEEN %s AND %s
        """
        params = [dt_from, dt_to]
        query += format_store_filter("si.store_id", store_id, params)
        query += format_employee_filter("si.employee_id", employee_id, params)
        query += " GROUP BY ci.customer_id, s.store_id ORDER BY total_spent DESC"
        return execute_raw_fetch_all(customerstorespendingserializer.DB_NAME, query, params)

class inventoryserializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None):
        query = """
        SELECT i.inventory_id, CONCAT(ii.make_name, ' ', vi.vehicle_model) AS vehicle_name, vi.vin, vi.mmr, s.store_name, CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
               CASE WHEN i.status = 1 THEN 'Sold' WHEN i.status = 2 THEN 'Pre-order' WHEN i.status = 0 THEN 'Unavailable' WHEN i.status = 4 THEN 'Available' ELSE 'Unknown' END AS status_label,
               i.sell_id AS selling_info, i.status, i.created_at, i.updated_at
        FROM inventory i
        INNER JOIN vehicle_info vi ON i.vehicle_id = vi.id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        INNER JOIN store s ON i.store_id = s.store_id
        INNER JOIN employee e ON i.employee_id = e.employee_id
        WHERE 1=1
        """
        params = []
        if store_id is not None:
            query += format_store_filter("i.store_id", store_id, params)
        query += format_employee_filter("i.employee_id", employee_id, params)
        if search:
            query += " AND (i.inventory_id LIKE %s OR vi.vehicle_model LIKE %s OR vi.vin LIKE %s OR ii.make_name LIKE %s OR s.store_name LIKE %s OR e.first_name LIKE %s OR e.last_name LIKE %s)"
            params.extend([f"%{search}%"] * 7)

        count_query = f"SELECT COUNT(*) FROM ({query}) AS temp"
        limit_clause = ""
        query_params = list(params)
        if limit is not None and limit >= 0:
            limit_clause = "LIMIT %s OFFSET %s"
            query_params.extend([limit, offset])
        query += f" ORDER BY i.inventory_id DESC {limit_clause}"

        with connections[inventoryserializer.DB_NAME].cursor() as cursor:
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
        data = execute_raw_fetch_all(inventoryserializer.DB_NAME, query, query_params)
        return total, data

    @staticmethod
    def fetch_one(inventory_id):
        return execute_fetchone_query(inventoryserializer.DB_NAME, "SELECT i.inventory_id, i.vehicle_id AS vehicle, vi.vin, i.store_id AS store, i.employee_id AS employee, i.status, i.sell_id AS selling_info FROM inventory i INNER JOIN vehicle_info vi ON i.vehicle_id = vi.id WHERE i.inventory_id = %s", [inventory_id])

    @staticmethod
    def create(vehicle_id, store_id, employee_id, status, selling_info=None):
        return execute_cud_query(inventoryserializer.DB_NAME, "INSERT INTO inventory (vehicle_id, store_id, employee_id, status, sell_id, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())", [vehicle_id, store_id, employee_id, status, selling_info])

    @staticmethod
    def update(inventory_id, vehicle_id, store_id, employee_id, status, selling_info=None):
        execute_cud_query(inventoryserializer.DB_NAME, "UPDATE inventory SET vehicle_id = %s, store_id = %s, employee_id = %s, status = %s, sell_id = %s, updated_at = NOW() WHERE inventory_id = %s", [vehicle_id, store_id, employee_id, status, selling_info, inventory_id])

    @staticmethod
    def delete(inventory_id):
        execute_cud_query(inventoryserializer.DB_NAME, "DELETE FROM inventory WHERE inventory_id = %s", [inventory_id])

    @staticmethod
    def create_from_request(data):
        vehicle = data.get('vehicle')
        store = data.get('store')
        employee = data.get('employee')
        status_val = data.get('status')
        selling_info = data.get('selling_info') or None
        if not vehicle or not store or not employee or status_val is None:
            raise ValueError("Vehicle, store, employee, and status are required fields.")
        new_id = inventoryserializer.create(vehicle, store, employee, status_val, selling_info)
        return inventoryserializer.fetch_one(new_id)

    @staticmethod
    def update_from_request(inventory_id, data):
        item = inventoryserializer.fetch_one(inventory_id)
        if not item:
            return None
        vehicle = data.get('vehicle', item['vehicle'])
        store = data.get('store', item['store'])
        employee = data.get('employee', item['employee'])
        status_val = data.get('status', item['status'])
        selling_info = data.get('selling_info', item['selling_info'])
        inventoryserializer.update(inventory_id, vehicle, store, employee, status_val, selling_info)
        return inventoryserializer.fetch_one(inventory_id)

    @staticmethod
    def delete_by_id(inventory_id):
        item = inventoryserializer.fetch_one(inventory_id)
        if not item:
            return False
        inventoryserializer.delete(inventory_id)
        return True

class CountrySerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        return execute_raw_sql_query(CountrySerializer.DB_NAME, "SELECT c.country_id, c.country_name, c.created_at, c.updated_at FROM country c WHERE 1=1", "SELECT COUNT(*) FROM country c WHERE 1=1", 'c', {}, ['country_name'], limit, offset, search, None, None, None, None, filters)
    @staticmethod
    def fetch_one(country_id):
        return execute_fetchone_query(CountrySerializer.DB_NAME, "SELECT c.country_id, c.country_name, c.created_at, c.updated_at FROM country c WHERE c.country_id = %s", [country_id])
    @staticmethod
    def create(country_name):
        return execute_cud_query(CountrySerializer.DB_NAME, "INSERT INTO country (country_name, created_at, updated_at) VALUES (%s, NOW(), NOW())", [country_name])
    @staticmethod
    def update(country_id, country_name):
        execute_cud_query(CountrySerializer.DB_NAME, "UPDATE country SET country_name = %s, updated_at = NOW() WHERE country_id = %s", [country_name, country_id])
    @staticmethod
    def delete(country_id):
        execute_cud_query(CountrySerializer.DB_NAME, "DELETE FROM country WHERE country_id = %s", [country_id])

class CitySerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        return execute_raw_sql_query(CitySerializer.DB_NAME, "SELECT ci.city_id, ci.city_name, ci.country_id AS country, co.country_name, ci.created_at, ci.updated_at FROM city ci INNER JOIN country co ON ci.country_id = co.country_id WHERE 1=1", "SELECT COUNT(*) FROM city ci INNER JOIN country co ON ci.country_id = co.country_id WHERE 1=1", 'ci', {'country': 'country_id'}, ['city_name', 'co.country_name'], limit, offset, search, None, None, None, None, filters)
    @staticmethod
    def fetch_one(city_id):
        return execute_fetchone_query(CitySerializer.DB_NAME, "SELECT ci.city_id, ci.city_name, ci.country_id AS country, co.country_name, ci.created_at, ci.updated_at FROM city ci INNER JOIN country co ON ci.country_id = co.country_id WHERE ci.city_id = %s", [city_id])
    @staticmethod
    def create(city_name, country):
        return execute_cud_query(CitySerializer.DB_NAME, "INSERT INTO city (city_name, country_id, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())", [city_name, country])
    @staticmethod
    def update(city_id, city_name, country):
        execute_cud_query(CitySerializer.DB_NAME, "UPDATE city SET city_name = %s, country_id = %s, updated_at = NOW() WHERE city_id = %s", [city_name, country, city_id])
    @staticmethod
    def delete(city_id):
        execute_cud_query(CitySerializer.DB_NAME, "DELETE FROM city WHERE city_id = %s", [city_id])

class StoreSerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        return execute_raw_sql_query(
            StoreSerializer.DB_NAME,
            "SELECT s.store_id, s.store_name, s.store_code, s.address, s.city_id AS city, s.country_id AS country, c.city_name, co.country_name, s.created_at, s.updated_at FROM store s INNER JOIN city c ON s.city_id = c.city_id INNER JOIN country co ON s.country_id = co.country_id WHERE 1=1",
            "SELECT COUNT(*) FROM store s INNER JOIN city c ON s.city_id = c.city_id INNER JOIN country co ON s.country_id = co.country_id WHERE 1=1",
            's', {'city': 'city_id', 'country': 'country_id'}, ['store_name', 'store_code', 'address', 'c.city_name', 'co.country_name'], limit, offset, search, store_id, None, 's.store_id', None, filters
        )
    @staticmethod
    def fetch_one(store_id):
        return execute_fetchone_query(StoreSerializer.DB_NAME, "SELECT s.store_id, s.store_name, s.store_code, s.address, s.city_id AS city, s.country_id AS country, c.city_name, co.country_name, s.created_at, s.updated_at FROM store s INNER JOIN city c ON s.city_id = c.city_id INNER JOIN country co ON s.country_id = co.country_id WHERE s.store_id = %s", [store_id])
    @staticmethod
    def create(store_name, store_code, address, city, country):
        return execute_cud_query(StoreSerializer.DB_NAME, "INSERT INTO store (store_name, store_code, address, city_id, country_id, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())", [store_name, store_code, address, city, country])
    @staticmethod
    def update(store_id, store_name, store_code, address, city, country):
        execute_cud_query(StoreSerializer.DB_NAME, "UPDATE store SET store_name = %s, store_code = %s, address = %s, city_id = %s, country_id = %s, updated_at = NOW() WHERE store_id = %s", [store_name, store_code, address, city, country, store_id])
    @staticmethod
    def delete(store_id):
        execute_cud_query(StoreSerializer.DB_NAME, "DELETE FROM store WHERE store_id = %s", [store_id])

class EmployeeRoleSerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        select_base = (
            "SELECT "
            "er.role_id, "
            "er.role_name, "
            "COALESCE("
            "  (SELECT eh.level FROM employee_hierarchy eh WHERE eh.role_id = er.role_id LIMIT 1),"
            "  CASE er.role_id"
            "    WHEN 10 THEN 1 WHEN 9 THEN 2 WHEN 8 THEN 3 WHEN 7 THEN 4 WHEN 6 THEN 5 "
            "    WHEN 5 THEN 6 WHEN 4 THEN 7 WHEN 3 THEN 8 WHEN 1 THEN 9 WHEN 2 THEN 9 "
            "    ELSE NULL"
            "  END"
            ") AS level, "
            "COALESCE("
            "  (SELECT el.notes FROM employee_level el WHERE el.level = (SELECT eh.level FROM employee_hierarchy eh WHERE eh.role_id = er.role_id LIMIT 1)),"
            "  CASE er.role_id"
            "    WHEN 10 THEN 'Top — No supervisor'"
            "    WHEN 9 THEN 'Reports to Pre-Owned Vehicle Specialist (role 10)'"
            "    WHEN 8 THEN 'Reports to Showroom Manager (role 9)'"
            "    WHEN 7 THEN 'Reports to Customer Relations Officer (role 8)'"
            "    WHEN 6 THEN 'Reports to Fleet Sales Specialist (role 7)'"
            "    WHEN 5 THEN 'Reports to Finance & Insurance Officer (role 6)'"
            "    WHEN 4 THEN 'Reports to Branch Manager (role 5)'"
            "    WHEN 3 THEN 'Reports to Regional Sales Manager (role 4)'"
            "    WHEN 1 THEN 'Reports to Sales Manager (role 3)'"
            "    WHEN 2 THEN 'Reports to Sales Manager (role 3)'"
            "    ELSE NULL"
            "  END"
            ") AS notes, "
            "(SELECT COUNT(*) FROM employee e WHERE e.employee_role = er.role_id) AS employee_count "
            "FROM employee_role er "
            "WHERE 1=1 ORDER BY er.role_id DESC"
        )
        count_base = "SELECT COUNT(*) FROM employee_role er WHERE 1=1"
        
        return execute_raw_sql_query(
            EmployeeRoleSerializer.DB_NAME,
            select_base,
            count_base,
            'er', {}, ['role_name'], limit, offset, search, None, None, None, None, filters
        )

    @staticmethod
    def fetch_one(role_id):
        query = (
            "SELECT "
            "er.role_id, "
            "er.role_name, "
            "COALESCE("
            "  (SELECT eh.level FROM employee_hierarchy eh WHERE eh.role_id = er.role_id LIMIT 1),"
            "  CASE er.role_id"
            "    WHEN 10 THEN 1 WHEN 9 THEN 2 WHEN 8 THEN 3 WHEN 7 THEN 4 WHEN 6 THEN 5 "
            "    WHEN 5 THEN 6 WHEN 4 THEN 7 WHEN 3 THEN 8 WHEN 1 THEN 9 WHEN 2 THEN 9 "
            "    ELSE NULL"
            "  END"
            ") AS level, "
            "COALESCE("
            "  (SELECT el.notes FROM employee_level el WHERE el.level = (SELECT eh.level FROM employee_hierarchy eh WHERE eh.role_id = er.role_id LIMIT 1)),"
            "  CASE er.role_id"
            "    WHEN 10 THEN 'Top — No supervisor'"
            "    WHEN 9 THEN 'Reports to Pre-Owned Vehicle Specialist (role 10)'"
            "    WHEN 8 THEN 'Reports to Showroom Manager (role 9)'"
            "    WHEN 7 THEN 'Reports to Customer Relations Officer (role 8)'"
            "    WHEN 6 THEN 'Reports to Fleet Sales Specialist (role 7)'"
            "    WHEN 5 THEN 'Reports to Finance & Insurance Officer (role 6)'"
            "    WHEN 4 THEN 'Reports to Branch Manager (role 5)'"
            "    WHEN 3 THEN 'Reports to Regional Sales Manager (role 4)'"
            "    WHEN 1 THEN 'Reports to Sales Manager (role 3)'"
            "    WHEN 2 THEN 'Reports to Sales Manager (role 3)'"
            "    ELSE NULL"
            "  END"
            ") AS notes, "
            "(SELECT COUNT(*) FROM employee e WHERE e.employee_role = er.role_id) AS employee_count "
            "FROM employee_role er "
            "WHERE er.role_id = %s"
        )
        return execute_fetchone_query(EmployeeRoleSerializer.DB_NAME, query, [role_id])
    @staticmethod
    def create(role_name):
        return execute_cud_query(EmployeeRoleSerializer.DB_NAME, "INSERT INTO employee_role (role_name, created_at, updated_at) VALUES (%s, NOW(), NOW())", [role_name])
    @staticmethod
    def update(role_id, role_name):
        execute_cud_query(EmployeeRoleSerializer.DB_NAME, "UPDATE employee_role SET role_name = %s, updated_at = NOW() WHERE role_id = %s", [role_name, role_id])
    @staticmethod
    def delete(role_id):
        execute_cud_query(EmployeeRoleSerializer.DB_NAME, "DELETE FROM employee_role WHERE role_id = %s", [role_id])


class EmployeeHierarchySerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        select_base = (
            "SELECT "
            "eh.employee_id, "
            "CONCAT(e.first_name, ' ', e.last_name) AS employee_name, "
            "er.role_name AS role_name, "
            "eh.level AS level, "
            "es.status AS status_name, "
            "CONCAT(s1.first_name, ' ', s1.last_name) AS supervisor_name "
            "FROM employee_hierarchy eh "
            "JOIN employee e ON eh.employee_id = e.employee_id "
            "JOIN employee_role er ON eh.role_id = er.role_id "
            "JOIN employee_status es ON eh.status_id = es.status_id "
            "LEFT JOIN employee s1 ON eh.supervisor_id = s1.employee_id "
            "WHERE 1=1 "
            "ORDER BY eh.employee_id DESC"
        )
        count_base = (
            "SELECT COUNT(*) "
            "FROM employee_hierarchy eh "
            "JOIN employee e ON eh.employee_id = e.employee_id "
            "JOIN employee_role er ON eh.role_id = er.role_id "
            "JOIN employee_status es ON eh.status_id = es.status_id "
            "LEFT JOIN employee s1 ON eh.supervisor_id = s1.employee_id "
            "WHERE 1=1"
        )
        
        field_map = {
            'employee_name': "CONCAT(e.first_name, ' ', e.last_name)",
            'role_name': 'er.role_name',
            'status_name': 'es.status',
            'supervisor_name': "CONCAT(s1.first_name, ' ', s1.last_name)",
        }
        
        search_fields = ['employee_name', 'role_name', 'supervisor_name']
        
        return execute_raw_sql_query(
            EmployeeHierarchySerializer.DB_NAME,
            select_base,
            count_base,
            'eh',
            field_map,
            search_fields,
            limit,
            offset,
            search,
            store_id,
            employee_id,
            'e.store_id',
            'eh.employee_id',
            filters
        )

    @staticmethod
    def fetch_one(employee_id):
        query = (
            "SELECT "
            "eh.employee_id, "
            "CONCAT(e.first_name, ' ', e.last_name) AS employee_name, "
            "er.role_name AS role_name, "
            "eh.level AS level, "
            "es.status AS status_name, "
            "eh.supervisor_id, CONCAT(s1.first_name, ' ', s1.last_name) AS supervisor_name, sr1.role_name AS supervisor_role_name, "
            "eh.supervisor2_id, CONCAT(s2.first_name, ' ', s2.last_name) AS supervisor2_name, sr2.role_name AS supervisor2_role_name, "
            "eh.supervisor3_id, CONCAT(s3.first_name, ' ', s3.last_name) AS supervisor3_name, sr3.role_name AS supervisor3_role_name, "
            "eh.supervisor4_id, CONCAT(s4.first_name, ' ', s4.last_name) AS supervisor4_name, sr4.role_name AS supervisor4_role_name, "
            "eh.supervisor5_id, CONCAT(s5.first_name, ' ', s5.last_name) AS supervisor5_name, sr5.role_name AS supervisor5_role_name, "
            "eh.supervisor6_id, CONCAT(s6.first_name, ' ', s6.last_name) AS supervisor6_name, sr6.role_name AS supervisor6_role_name, "
            "eh.supervisor7_id, CONCAT(s7.first_name, ' ', s7.last_name) AS supervisor7_name, sr7.role_name AS supervisor7_role_name, "
            "eh.supervisor8_id, CONCAT(s8.first_name, ' ', s8.last_name) AS supervisor8_name, sr8.role_name AS supervisor8_role_name "
            "FROM employee_hierarchy eh "
            "JOIN employee e ON eh.employee_id = e.employee_id "
            "JOIN employee_role er ON eh.role_id = er.role_id "
            "JOIN employee_status es ON eh.status_id = es.status_id "
            "LEFT JOIN employee s1 ON eh.supervisor_id = s1.employee_id "
            "LEFT JOIN employee_role sr1 ON eh.supervisor_role_id = sr1.role_id "
            "LEFT JOIN employee s2 ON eh.supervisor2_id = s2.employee_id "
            "LEFT JOIN employee_role sr2 ON eh.supervisor2_role_id = sr2.role_id "
            "LEFT JOIN employee s3 ON eh.supervisor3_id = s3.employee_id "
            "LEFT JOIN employee_role sr3 ON eh.supervisor3_role_id = sr3.role_id "
            "LEFT JOIN employee s4 ON eh.supervisor4_id = s4.employee_id "
            "LEFT JOIN employee_role sr4 ON eh.supervisor4_role_id = sr4.role_id "
            "LEFT JOIN employee s5 ON eh.supervisor5_id = s5.employee_id "
            "LEFT JOIN employee_role sr5 ON eh.supervisor5_role_id = sr5.role_id "
            "LEFT JOIN employee s6 ON eh.supervisor6_id = s6.employee_id "
            "LEFT JOIN employee_role sr6 ON eh.supervisor6_role_id = sr6.role_id "
            "LEFT JOIN employee s7 ON eh.supervisor7_id = s7.employee_id "
            "LEFT JOIN employee_role sr7 ON eh.supervisor7_role_id = sr7.role_id "
            "LEFT JOIN employee s8 ON eh.supervisor8_id = s8.employee_id "
            "LEFT JOIN employee_role sr8 ON eh.supervisor8_role_id = sr8.role_id "
            "WHERE eh.employee_id = %s"
        )
        return execute_fetchone_query(EmployeeHierarchySerializer.DB_NAME, query, [employee_id])


class EmployeeStatusSerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        return execute_raw_sql_query(
            EmployeeStatusSerializer.DB_NAME,
            "SELECT es.status_id, es.status, es.created_at, es.updated_at, (SELECT COUNT(*) FROM employee e WHERE e.status = es.status_id) AS employee_count FROM employee_status es WHERE 1=1",
            "SELECT COUNT(*) FROM employee_status es WHERE 1=1",
            'es', {}, ['status'], limit, offset, search, None, None, None, None, filters
        )
    @staticmethod
    def fetch_one(status_id):
        return execute_fetchone_query(EmployeeStatusSerializer.DB_NAME, "SELECT es.status_id, es.status, es.created_at, es.updated_at, (SELECT COUNT(*) FROM employee e WHERE e.status = es.status_id) AS employee_count FROM employee_status es WHERE es.status_id = %s", [status_id])
    @staticmethod
    def create(status):
        return execute_cud_query(EmployeeStatusSerializer.DB_NAME, "INSERT INTO employee_status (status, created_at, updated_at) VALUES (%s, NOW(), NOW())", [status])
    @staticmethod
    def update(status_id, status):
        execute_cud_query(EmployeeStatusSerializer.DB_NAME, "UPDATE employee_status SET status = %s, updated_at = NOW() WHERE status_id = %s", [status, status_id])
    @staticmethod
    def delete(status_id):
        execute_cud_query(EmployeeStatusSerializer.DB_NAME, "DELETE FROM employee_status WHERE status_id = %s", [status_id])

class IndustryInfoSerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        return execute_raw_sql_query(
            IndustryInfoSerializer.DB_NAME,
            "SELECT ii.make_id, ii.make_name, ii.created_at, ii.updated_at, (SELECT COUNT(*) FROM vehicle_info vi WHERE vi.make_id = ii.make_id) AS vehicle_count FROM industry_info ii WHERE 1=1",
            "SELECT COUNT(*) FROM industry_info ii WHERE 1=1",
            'ii', {}, ['make_name'], limit, offset, search, None, None, None, None, filters
        )
    @staticmethod
    def fetch_one(make_id):
        return execute_fetchone_query(IndustryInfoSerializer.DB_NAME, "SELECT ii.make_id, ii.make_name, ii.created_at, ii.updated_at, (SELECT COUNT(*) FROM vehicle_info vi WHERE vi.make_id = ii.make_id) AS vehicle_count FROM industry_info ii WHERE ii.make_id = %s", [make_id])
    @staticmethod
    def create(make_name):
        return execute_cud_query(IndustryInfoSerializer.DB_NAME, "INSERT INTO industry_info (make_name, created_at, updated_at) VALUES (%s, NOW(), NOW())", [make_name])
    @staticmethod
    def update(make_id, make_name):
        execute_cud_query(IndustryInfoSerializer.DB_NAME, "UPDATE industry_info SET make_name = %s, updated_at = NOW() WHERE make_id = %s", [make_name, make_id])
    @staticmethod
    def delete(make_id):
        execute_cud_query(IndustryInfoSerializer.DB_NAME, "DELETE FROM industry_info WHERE make_id = %s", [make_id])

class VehicleInfoSerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        return execute_raw_sql_query(
            VehicleInfoSerializer.DB_NAME,
            "SELECT vi.id, vi.vehicle_model, vi.make_id AS make, vi.mmr, vi.trim, vi.body, vi.transmission, vi.vin, vi.state, vi.condition, vi.odometer, vi.color, vi.interior, ii.make_name, vi.created_at, vi.updated_at FROM vehicle_info vi INNER JOIN industry_info ii ON vi.make_id = ii.make_id WHERE 1=1 ORDER BY vi.id DESC",
            "SELECT COUNT(*) FROM vehicle_info vi INNER JOIN industry_info ii ON vi.make_id = ii.make_id WHERE 1=1",
            'vi', {'make': 'make_id'}, ['vehicle_model', 'ii.make_name', 'vin', 'color'], limit, offset, search, None, None, None, None, filters
        )
    @staticmethod
    def fetch_one(vehicle_id):
        return execute_fetchone_query(VehicleInfoSerializer.DB_NAME, "SELECT vi.id, vi.vehicle_model, vi.make_id AS make, vi.mmr, vi.trim, vi.body, vi.transmission, vi.vin, vi.state, vi.condition, vi.odometer, vi.color, vi.interior, ii.make_name, vi.created_at, vi.updated_at FROM vehicle_info vi INNER JOIN industry_info ii ON vi.make_id = ii.make_id WHERE vi.id = %s", [vehicle_id])
    @staticmethod
    def create(vehicle_model, make, mmr, trim=None, body=None, transmission=None, vin=None, state=None, condition=None, odometer=None, color=None, interior=None):
        return execute_cud_query(VehicleInfoSerializer.DB_NAME, "INSERT INTO vehicle_info (vehicle_model, make_id, mmr, trim, body, transmission, vin, state, `condition`, odometer, color, interior, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())", [vehicle_model, make, mmr, trim, body, transmission, vin, state, condition, odometer, color, interior])
    @staticmethod
    def update(id, vehicle_model, make, mmr, trim=None, body=None, transmission=None, vin=None, state=None, condition=None, odometer=None, color=None, interior=None):
        execute_cud_query(VehicleInfoSerializer.DB_NAME, "UPDATE vehicle_info SET vehicle_model = %s, make_id = %s, mmr = %s, trim = %s, body = %s, transmission = %s, vin = %s, state = %s, `condition` = %s, odometer = %s, color = %s, interior = %s, updated_at = NOW() WHERE id = %s", [vehicle_model, make, mmr, trim, body, transmission, vin, state, condition, odometer, color, interior, id])
    @staticmethod
    def delete(vehicle_id):
        execute_cud_query(VehicleInfoSerializer.DB_NAME, "DELETE FROM vehicle_info WHERE id = %s", [vehicle_id])

class CustomerInfoSerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        where_clauses = ["1=1"]
        params = []
        if store_id is not None:
            store_clause = format_store_filter("si.store_id", store_id, params)
            where_clauses.append(
                "EXISTS (SELECT 1 FROM selling_info si WHERE si.customer_id = ci.customer_id" + store_clause + ")"
            )
        if employee_id is not None:
            if isinstance(employee_id, (list, tuple, set)):
                if len(employee_id) == 1:
                    where_clauses.append("EXISTS (SELECT 1 FROM selling_info si WHERE si.customer_id = ci.customer_id AND si.employee_id = %s)")
                    params.append(list(employee_id)[0])
                elif len(employee_id) > 1:
                    placeholders = ", ".join(["%s"] * len(employee_id))
                    where_clauses.append(f"EXISTS (SELECT 1 FROM selling_info si WHERE si.customer_id = ci.customer_id AND si.employee_id IN ({placeholders}))")
                    params.extend(employee_id)
                else:
                    where_clauses.append("1=0")
            else:
                where_clauses.append("EXISTS (SELECT 1 FROM selling_info si WHERE si.customer_id = ci.customer_id AND si.employee_id = %s)")
                params.append(employee_id)

        field_map = {'city': 'ci.city_id', 'country': 'ci.country_id'}
        for key, val in filters.items():
            if val is not None and val != '':
                col = field_map.get(key, f"ci.{key}")
                where_clauses.append(f"{col} = %s")
                params.append(val)

        if search:
            search_param = f"%{search}%"
            search_clauses = ["ci.firstname LIKE %s", "ci.lastname LIKE %s", "ci.customer_status LIKE %s", "ci.customer_address LIKE %s", "CONCAT(ci.firstname, ' ', ci.lastname) LIKE %s"]
            params.extend([search_param] * 5)
            where_clauses.append("(" + " OR ".join(search_clauses) + ")")

        where_str = " AND ".join(where_clauses)
        limit_clause = ""
        query_params = list(params)
        if limit is not None and limit >= 0:
            limit_clause = "LIMIT %s OFFSET %s"
            query_params.extend([limit, offset])

        select_query = f"""
        SELECT ci.customer_id, ci.firstname, ci.lastname, ci.customer_status, ci.customer_address, ci.city_id AS city, ci.country_id AS country,
               c.city_name, co.country_name, ci.created_at, ci.updated_at
        FROM customer_info ci
        INNER JOIN city c ON ci.city_id = c.city_id
        INNER JOIN country co ON ci.country_id = co.country_id
        WHERE {where_str}
        ORDER BY ci.customer_id DESC
        {limit_clause}
        """
        count_query = f"SELECT COUNT(*) FROM customer_info ci INNER JOIN city c ON ci.city_id = c.city_id INNER JOIN country co ON ci.country_id = co.country_id WHERE {where_str}"

        with connections[CustomerInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
        data = execute_raw_fetch_all(CustomerInfoSerializer.DB_NAME, select_query, query_params)
        return total, data

    @staticmethod
    def fetch_one(customer_id):
        return execute_fetchone_query(CustomerInfoSerializer.DB_NAME, "SELECT ci.customer_id, ci.firstname, ci.lastname, ci.customer_status, ci.customer_address, ci.city_id AS city, ci.country_id AS country, c.city_name, co.country_name, ci.created_at, ci.updated_at FROM customer_info ci INNER JOIN city c ON ci.city_id = c.city_id INNER JOIN country co ON ci.country_id = co.country_id WHERE ci.customer_id = %s", [customer_id])

    @staticmethod
    def create(firstname, lastname, customer_status, customer_address, city, country):
        return execute_cud_query(CustomerInfoSerializer.DB_NAME, "INSERT INTO customer_info (firstname, lastname, customer_status, customer_address, city_id, country_id, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())", [firstname, lastname, customer_status, customer_address, city, country])

    @staticmethod
    def update(customer_id, firstname, lastname, customer_status, customer_address, city, country):
        execute_cud_query(CustomerInfoSerializer.DB_NAME, "UPDATE customer_info SET firstname = %s, lastname = %s, customer_status = %s, customer_address = %s, city_id = %s, country_id = %s, updated_at = NOW() WHERE customer_id = %s", [firstname, lastname, customer_status, customer_address, city, country, customer_id])

    @staticmethod
    def delete(customer_id):
        execute_cud_query(CustomerInfoSerializer.DB_NAME, "DELETE FROM customer_info WHERE customer_id = %s", [customer_id])

class SellingInfoSerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        where_clauses = ["1=1"]
        params = []
        add_store_clause(where_clauses, params, "si.store_id", store_id)
        add_employee_clause(where_clauses, params, "si.employee_id", employee_id)

        field_map = {'customer': 'si.customer_id', 'vehicle': 'si.vehicle_id', 'employee': 'si.employee_id', 'store': 'si.store_id'}
        for key, val in filters.items():
            if val is not None and val != '':
                col = field_map.get(key, f"si.{key}")
                where_clauses.append(f"{col} = %s")
                params.append(val)

        if search:
            search_param = f"%{search}%"
            where_clauses.append("""(
                CAST(si.sell_id AS CHAR) LIKE %s OR si.selling_price LIKE %s OR si.selling_date LIKE %s OR
                vi.vehicle_model LIKE %s OR ii.make_name LIKE %s OR e.first_name LIKE %s OR e.last_name LIKE %s OR
                s.store_name LIKE %s OR CONCAT(e.first_name, ' ', e.last_name) LIKE %s OR CONCAT(ci.firstname, ' ', ci.lastname) LIKE %s
            )""")
            params.extend([search_param] * 10)

        where_str = " AND ".join(where_clauses)
        limit_clause = ""
        query_params = list(params)
        if limit is not None and limit >= 0:
            limit_clause = "LIMIT %s OFFSET %s"
            query_params.extend([limit, offset])

        select_query = f"""
        SELECT si.sell_id, si.customer_id AS customer, si.vehicle_id AS vehicle, si.employee_id AS employee, si.store_id AS store, si.selling_price, si.selling_date,
               CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name, CONCAT(ii.make_name, ' ', vi.vehicle_model) AS vehicle_name,
               CONCAT(e.first_name, ' ', e.last_name) AS employee_name, s.store_name, si.created_at, si.updated_at
        FROM selling_info si
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        INNER JOIN employee e ON si.employee_id = e.employee_id
        INNER JOIN store s ON si.store_id = s.store_id
        WHERE {where_str}
        ORDER BY si.sell_id DESC
        {limit_clause}
        """
        count_query = f"""
        SELECT COUNT(*) FROM selling_info si
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        INNER JOIN employee e ON si.employee_id = e.employee_id
        INNER JOIN store s ON si.store_id = s.store_id
        WHERE {where_str}
        """
        with connections[SellingInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
        data = execute_raw_fetch_all(SellingInfoSerializer.DB_NAME, select_query, query_params)
        return total, data

    @staticmethod
    def fetch_one(sell_id):
        return execute_fetchone_query(SellingInfoSerializer.DB_NAME, "SELECT sell_id, customer_id AS customer, vehicle_id AS vehicle, employee_id AS employee, store_id AS store, selling_price, selling_date, created_at, updated_at FROM selling_info WHERE sell_id = %s", [sell_id])

    @staticmethod
    def create(customer, vehicle, employee, store, selling_price, selling_date):
        return execute_cud_query(SellingInfoSerializer.DB_NAME, "INSERT INTO selling_info (customer_id, vehicle_id, employee_id, store_id, selling_price, selling_date, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())", [customer, vehicle, employee, store, selling_price, selling_date])

    @staticmethod
    def update(sell_id, customer, vehicle, employee, store, selling_price, selling_date):
        execute_cud_query(SellingInfoSerializer.DB_NAME, "UPDATE selling_info SET customer_id = %s, vehicle_id = %s, employee_id = %s, store_id = %s, selling_price = %s, selling_date = %s, updated_at = NOW() WHERE sell_id = %s", [customer, vehicle, employee, store, selling_price, selling_date, sell_id])

    @staticmethod
    def delete(sell_id):
        execute_cud_query(SellingInfoSerializer.DB_NAME, "DELETE FROM selling_info WHERE sell_id = %s", [sell_id])

    @staticmethod
    def fetch_dashboard_stats(store_id=None, employee_id=None):
        where_clauses = ["1=1"]
        params = []
        add_store_clause(where_clauses, params, "si.store_id", store_id)
        add_employee_clause(where_clauses, params, "si.employee_id", employee_id)
        where_str = " AND ".join(where_clauses)

        stats_query = f"SELECT COUNT(si.sell_id), SUM(si.selling_price) FROM selling_info si WHERE {where_str}"
        if store_id is not None or employee_id is not None:
            cust_query = f"SELECT COUNT(DISTINCT si.customer_id) FROM selling_info si WHERE {where_str}"
            cust_params = params
        else:
            cust_query = "SELECT COUNT(*) FROM customer_info"
            cust_params = []
        recent_query = f"""
            SELECT si.sell_id, CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name, CONCAT(ii.make_name, ' ', vi.vehicle_model) AS vehicle_name,
                   CONCAT(e.first_name, ' ', e.last_name) AS employee_name, si.selling_price, si.selling_date
            FROM selling_info si
            INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
            INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
            INNER JOIN industry_info ii ON vi.make_id = ii.make_id
            INNER JOIN employee e ON si.employee_id = e.employee_id
            WHERE {where_str} ORDER BY si.selling_date DESC, si.sell_id DESC LIMIT 5
        """
        top_query = f"""
            SELECT ii.make_name AS brand_name, COUNT(si.sell_id) AS count, SUM(si.selling_price) AS revenue
            FROM selling_info si
            INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
            INNER JOIN industry_info ii ON vi.make_id = ii.make_id
            WHERE {where_str} GROUP BY ii.make_id, ii.make_name ORDER BY count DESC LIMIT 5
        """
        monthly_query = f"""
            SELECT DATE_FORMAT(si.selling_date, '%%Y-%%m-01') AS month, COUNT(si.sell_id) AS count, SUM(si.selling_price) AS revenue
            FROM selling_info si
            WHERE {where_str} GROUP BY DATE_FORMAT(si.selling_date, '%%Y-%%m-01') ORDER BY month ASC
        """
        with connections[SellingInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(stats_query, params)
            row = cursor.fetchone()
            sales_count = row[0] or 0
            total_revenue = float(row[1] or 0)

            cursor.execute(cust_query, cust_params)
            customers_count = cursor.fetchone()[0] or 0

            cursor.execute(recent_query, params)
            cols_r = [col[0] for col in cursor.description]
            recent_sales = [format_date_fields(dict(zip(cols_r, r))) for r in cursor.fetchall()]

            cursor.execute(top_query, params)
            cols_t = [col[0] for col in cursor.description]
            top_selling = [dict(zip(cols_t, r)) for r in cursor.fetchall()]

            cursor.execute(monthly_query, params)
            cols_m = [col[0] for col in cursor.description]
            monthly_sales = [dict(zip(cols_m, r)) for r in cursor.fetchall()]

        chart_dates, chart_sales, chart_revenue = [], [], []
        for item in monthly_sales:
            try:
                dt = datetime.datetime.strptime(item['month'], '%Y-%m-%d') if isinstance(item['month'], str) else item['month']
                chart_dates.append(dt.strftime('%b %Y'))
            except Exception:
                chart_dates.append(str(item['month']))
            chart_sales.append(item['count'])
            chart_revenue.append(float(item['revenue'] or 0))

        pending_orders = []
        try:
            from ecommerce.models import Order
            all_pending_qs = Order.objects.filter(
                order_status__in=[Order.OrderStatus.NEEDS_APPROVAL, Order.OrderStatus.PARTIALLY_PAID]
            )
            total_pending_count = all_pending_qs.count()
            orders_qs = all_pending_qs

            if store_id is not None:
                store_qs = all_pending_qs.filter(store_id=store_id)
                if store_qs.exists():
                    orders_qs = store_qs
                    total_pending_count = store_qs.count()

            orders_qs = orders_qs.select_related('customer', 'customer__info', 'inventory', 'inventory__vehicle', 'inventory__vehicle__make', 'store').order_by('-order_id')
            for o in orders_qs:
                c_info = getattr(o.customer, 'info', None)
                c_name = f"{c_info.firstname} {c_info.lastname}" if c_info and c_info.firstname else o.customer.email
                v_make = o.inventory.vehicle.make.make_name if o.inventory and o.inventory.vehicle and o.inventory.vehicle.make else ""
                v_model = o.inventory.vehicle.vehicle_model if o.inventory and o.inventory.vehicle else "Vehicle"
                v_name = f"{v_make} {v_model}".strip()
                pending_orders.append({
                    'order_id': o.order_id,
                    'customer_name': c_name,
                    'vehicle_name': v_name,
                    'total_amount': o.total_amount,
                    'order_status': o.order_status,
                    'order_status_display': o.get_order_status_display(),
                    'fulfillment_type_display': o.get_fulfillment_type_display(),
                    'payment_preference_display': o.get_payment_preference_display(),
                    'delivery_address': o.delivery_address or '',
                    'store_name': o.store.store_name if o.store else "Store",
                })
        except Exception as e:
            print("Error fetching pending_orders:", e)
            pending_orders = []
            total_pending_count = 0

        return {
            'sales_count': sales_count,
            'total_revenue': total_revenue,
            'customers_count': customers_count,
            'recent_sales': recent_sales,
            'top_selling': top_selling,
            'chart_dates': chart_dates,
            'chart_sales': chart_sales,
            'chart_revenue': chart_revenue,
            'pending_orders': pending_orders,
            'total_pending_count': total_pending_count,
        }

class EmployeeBudgetSerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        where_clauses = ["1=1"]
        params = []
        add_store_clause(where_clauses, params, "eb.store_id", store_id)
        add_employee_clause(where_clauses, params, "eb.employee_id", employee_id)

        field_map = {'employee': 'eb.employee_id', 'store': 'eb.store_id', 'budget_year': 'eb.budget_year', 'budget_month': 'eb.budget_month'}
        for key, val in filters.items():
            if val is not None and val != '':
                col = field_map.get(key, f"eb.{key}")
                where_clauses.append(f"{col} = %s")
                params.append(val)

        if search:
            search_param = f"%{search}%"
            where_clauses.append("(e.first_name LIKE %s OR e.last_name LIKE %s OR s.store_name LIKE %s OR eb.budget_year LIKE %s OR CONCAT(e.first_name, ' ', e.last_name) LIKE %s)")
            params.extend([search_param] * 5)

        where_str = " AND ".join(where_clauses)
        limit_clause = ""
        query_params = list(params)
        if limit is not None and limit >= 0:
            limit_clause = "LIMIT %s OFFSET %s"
            query_params.extend([limit, offset])

        select_query = f"""
        SELECT eb.id, eb.employee_id AS employee, eb.budget_year, eb.budget_month, eb.store_id AS store, eb.budget_qty, eb.budget_amount,
               CONCAT(e.first_name, ' ', e.last_name) AS employee_name, s.store_name, eb.created_at, eb.updated_at
        FROM employee_budget eb
        INNER JOIN employee e ON eb.employee_id = e.employee_id
        INNER JOIN store s ON eb.store_id = s.store_id
        WHERE {where_str}
        ORDER BY eb.id DESC
        {limit_clause}
        """
        count_query = f"SELECT COUNT(*) FROM employee_budget eb INNER JOIN employee e ON eb.employee_id = e.employee_id INNER JOIN store s ON eb.store_id = s.store_id WHERE {where_str}"

        with connections[EmployeeBudgetSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
        data = execute_raw_fetch_all(EmployeeBudgetSerializer.DB_NAME, select_query, query_params)
        return total, data

    @staticmethod
    def fetch_one(budget_id):
        return execute_fetchone_query(EmployeeBudgetSerializer.DB_NAME, "SELECT eb.id, eb.employee_id AS employee, eb.budget_year, eb.budget_month, eb.store_id AS store, eb.budget_qty, eb.budget_amount, CONCAT(e.first_name, ' ', e.last_name) AS employee_name, s.store_name, eb.created_at, eb.updated_at FROM employee_budget eb INNER JOIN employee e ON eb.employee_id = e.employee_id INNER JOIN store s ON eb.store_id = s.store_id WHERE eb.id = %s", [budget_id])

    @staticmethod
    def create(employee, budget_year, budget_month, store, budget_qty, budget_amount):
        return execute_cud_query(EmployeeBudgetSerializer.DB_NAME, "INSERT INTO employee_budget (employee_id, budget_year, budget_month, store_id, budget_qty, budget_amount, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())", [employee, budget_year, budget_month, store, budget_qty, budget_amount])

    @staticmethod
    def update(id, employee, budget_year, budget_month, store, budget_qty, budget_amount):
        execute_cud_query(EmployeeBudgetSerializer.DB_NAME, "UPDATE employee_budget SET employee_id = %s, budget_year = %s, budget_month = %s, store_id = %s, budget_qty = %s, budget_amount = %s, updated_at = NOW() WHERE id = %s", [employee, budget_year, budget_month, store, budget_qty, budget_amount, id])

    @staticmethod
    def delete(budget_id):
        execute_cud_query(EmployeeBudgetSerializer.DB_NAME, "DELETE FROM employee_budget WHERE id = %s", [budget_id])

    @staticmethod
    def get_distinct_years():
        query = "SELECT DISTINCT budget_year FROM employee_budget ORDER BY budget_year DESC"
        with connections[EmployeeBudgetSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def fetch_stats(budget_year=None):
        query = "SELECT COUNT(id) AS total_count, COALESCE(SUM(budget_amount), 0) AS total_sum, COALESCE(AVG(budget_amount), 0) AS avg_amount FROM employee_budget"
        params = []
        if budget_year:
            query += " WHERE budget_year = %s"
            params.append(budget_year)
        with connections[EmployeeBudgetSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return {
                "total_count": row[0] or 0,
                "total_sum": float(row[1] or 0),
                "avg_amount": float(row[2] or 0)
            }

class EmployeeSerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        where_clauses = ["1=1"]
        params = []
        add_store_clause(where_clauses, params, "e.store_id", store_id)
        add_employee_clause(where_clauses, params, "e.employee_id", employee_id)

        field_map = {'employee_role': 'e.employee_role', 'status': 'e.status', 'store': 'e.store_id', 'city': 'e.city_id', 'country': 'e.country_id'}
        for key, val in filters.items():
            if val is not None and val != '':
                col = field_map.get(key, f"e.{key}")
                where_clauses.append(f"{col} = %s")
                params.append(val)

        if search:
            search_param = f"%{search}%"
            where_clauses.append("(e.first_name LIKE %s OR e.last_name LIKE %s OR s.store_name LIKE %s OR er.role_name LIKE %s OR CONCAT(e.first_name, ' ', e.last_name) LIKE %s)")
            params.extend([search_param] * 5)

        where_str = " AND ".join(where_clauses)
        limit_clause = ""
        query_params = list(params)
        if limit is not None and limit >= 0:
            limit_clause = "LIMIT %s OFFSET %s"
            query_params.extend([limit, offset])

        select_query = f"""
        SELECT e.employee_id, e.first_name, e.last_name, e.date_of_joining, e.employee_addr,
               e.employee_role, e.status, e.store_id AS store, e.city_id AS city, e.country_id AS country,
               er.role_name, es.status AS status_name, s.store_name, ci.city_name, co.country_name, e.created_at, e.updated_at
        FROM employee e
        INNER JOIN employee_role er ON e.employee_role = er.role_id
        INNER JOIN employee_status es ON e.status = es.status_id
        INNER JOIN store s ON e.store_id = s.store_id
        INNER JOIN city ci ON e.city_id = ci.city_id
        INNER JOIN country co ON e.country_id = co.country_id
        WHERE {where_str}
        ORDER BY e.employee_id DESC
        {limit_clause}
        """
        count_query = f"SELECT COUNT(*) FROM employee e INNER JOIN employee_role er ON e.employee_role = er.role_id INNER JOIN employee_status es ON e.status = es.status_id INNER JOIN store s ON e.store_id = s.store_id INNER JOIN city ci ON e.city_id = ci.city_id INNER JOIN country co ON e.country_id = co.country_id WHERE {where_str}"

        with connections[EmployeeSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
        data = execute_raw_fetch_all(EmployeeSerializer.DB_NAME, select_query, query_params)
        return total, data

    @staticmethod
    def fetch_one(employee_id):
        return execute_fetchone_query(EmployeeSerializer.DB_NAME, "SELECT e.employee_id, e.first_name, e.last_name, e.date_of_joining, e.employee_addr, e.employee_role, e.status, e.store_id AS store, e.city_id AS city, e.country_id AS country, er.role_name, es.status AS status_name, s.store_name, ci.city_name, co.country_name, e.created_at, e.updated_at FROM employee e INNER JOIN employee_role er ON e.employee_role = er.role_id INNER JOIN employee_status es ON e.status = es.status_id INNER JOIN store s ON e.store_id = s.store_id INNER JOIN city ci ON e.city_id = ci.city_id INNER JOIN country co ON e.country_id = co.country_id WHERE e.employee_id = %s", [employee_id])

    @staticmethod
    def create(first_name, last_name, date_of_joining, employee_addr, employee_role, status, store, city, country, password=None):
        if not password:
            password = 'CAr$@lse2014'
        return execute_cud_query(EmployeeSerializer.DB_NAME, "INSERT INTO employee (first_name, last_name, date_of_joining, employee_addr, employee_role, status, store_id, city_id, country_id, password, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())", [first_name, last_name, date_of_joining, employee_addr, employee_role, status, store, city, country, password])

    @staticmethod
    def update(employee_id, first_name, last_name, date_of_joining, employee_addr, employee_role, status, store, city, country, password=None):
        if password:
            query = "UPDATE employee SET first_name = %s, last_name = %s, date_of_joining = %s, employee_addr = %s, employee_role = %s, status = %s, store_id = %s, city_id = %s, country_id = %s, password = %s, updated_at = NOW() WHERE employee_id = %s"
            params = [first_name, last_name, date_of_joining, employee_addr, employee_role, status, store, city, country, password, employee_id]
        else:
            query = "UPDATE employee SET first_name = %s, last_name = %s, date_of_joining = %s, employee_addr = %s, employee_role = %s, status = %s, store_id = %s, city_id = %s, country_id = %s, updated_at = NOW() WHERE employee_id = %s"
            params = [first_name, last_name, date_of_joining, employee_addr, employee_role, status, store, city, country, employee_id]
        execute_cud_query(EmployeeSerializer.DB_NAME, query, params)

    @staticmethod
    def delete(employee_id):
        execute_cud_query(EmployeeSerializer.DB_NAME, "DELETE FROM employee WHERE employee_id = %s", [employee_id])

class budgetvssalesserializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(dt_from, dt_to):
        try:
            year_val = int(dt_from.split('-')[0])
            month_val = int(dt_from.split('-')[1])
        except (ValueError, TypeError, IndexError):
            year_val, month_val = 2014, 12

        query = """
        SELECT si.employee_id, e.first_name, e.last_name, s.store_id, s.store_name, SUM(si.selling_price) AS sell_value, eb.budget_amount as budget
        FROM selling_info si 
        LEFT JOIN employee e on si.employee_id=e.employee_id 
        INNER JOIN employee_budget eb ON si.employee_id=eb.employee_id 
        LEFT JOIN store s on eb.store_id=s.store_id
        WHERE eb.budget_year = %s and eb.budget_month = %s AND si.selling_date BETWEEN %s AND %s 
        GROUP BY si.employee_id, e.first_name, e.last_name, s.store_id, s.store_name, eb.budget_amount
        ORDER BY si.employee_id DESC
        """
        data = execute_raw_fetch_all(budgetvssalesserializer.DB_NAME, query, [year_val, month_val, dt_from, dt_to])
        for item in data:
            sell_value = float(item['sell_value']) if item['sell_value'] is not None else 0.0
            budget = float(item['budget']) if item['budget'] is not None else 0.0
            item['sell_value'] = sell_value
            item['budget'] = budget
            item['difference'] = sell_value - budget
            item['achievement'] = round((sell_value / budget) * 100, 2) if budget > 0 else 0.00
        return data

class InvoiceSerializer:
    DB_NAME = 'default'
    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        where_clauses = ['1=1']
        params = []
        add_store_clause(where_clauses, params, 'si.store_id', store_id)
        add_employee_clause(where_clauses, params, "si.employee_id", employee_id)

        field_map = {'payment_status': 'inv.payment_status', 'payment_method': 'inv.payment_method', 'sell_id': 'inv.sell_id'}
        for key, val in filters.items():
            if val is not None and val != '':
                col = field_map.get(key, f'inv.{key}')
                where_clauses.append(f'{col} = %s')
                params.append(val)

        if search:
            search_param = f'%{search}%'
            where_clauses.append("""(
                CAST(inv.invoice_id AS CHAR) LIKE %s OR CONCAT(ci.firstname, ' ', ci.lastname) LIKE %s OR ci.customer_address LIKE %s OR
                CONCAT(ii.make_name, ' ', vi.vehicle_model) LIKE %s OR vi.vin LIKE %s OR CONCAT(e.first_name, ' ', e.last_name) LIKE %s OR
                s.store_name LIKE %s OR s.address LIKE %s OR inv.payment_status LIKE %s OR inv.payment_method LIKE %s OR
                CAST(inv.invoice_date AS CHAR) LIKE %s
            )""")
            params.extend([search_param] * 11)

        where_str = ' AND '.join(where_clauses)
        limit_clause = ""
        query_params = list(params)
        if limit is not None and limit >= 0:
            limit_clause = "LIMIT %s OFFSET %s"
            query_params.extend([limit, offset])

        select_query = f"""
        SELECT inv.invoice_id, inv.sell_id, inv.invoice_date, inv.due_date, inv.payment_status, inv.payment_method, inv.mmr, inv.discount_amount, inv.discount_pct, inv.notes, inv.created_at, inv.updated_at,
               si.selling_price, si.selling_date, (si.selling_price - inv.discount_amount) AS final_amount, CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name, ci.customer_address,
               CONCAT(ii.make_name, ' ', vi.vehicle_model) AS vehicle_name, vi.vin, CONCAT(e.first_name, ' ', e.last_name) AS employee_name, er.role_name AS employee_role, s.store_name, s.address AS store_address
        FROM invoice inv
        INNER JOIN selling_info si  ON inv.sell_id = si.sell_id
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN vehicle_info vi  ON si.vehicle_id = vi.id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        INNER JOIN employee e       ON si.employee_id = e.employee_id
        INNER JOIN employee_role er ON e.employee_role = er.role_id
        INNER JOIN store s          ON si.store_id = s.store_id
        WHERE {where_str} ORDER BY inv.invoice_date DESC, inv.invoice_id DESC {limit_clause}
        """
        count_query = f"""
        SELECT COUNT(*) FROM invoice inv
        INNER JOIN selling_info si  ON inv.sell_id = si.sell_id
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN vehicle_info vi  ON si.vehicle_id = vi.id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        INNER JOIN employee e       ON si.employee_id = e.employee_id
        INNER JOIN store s          ON si.store_id = s.store_id
        WHERE {where_str}
        """

        with connections[InvoiceSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
        data = execute_raw_fetch_all(InvoiceSerializer.DB_NAME, select_query, query_params)
        return total, data

    @staticmethod
    def fetch_one(invoice_id):
        query = """
        SELECT inv.invoice_id, inv.sell_id, inv.invoice_date, inv.due_date, inv.payment_status, inv.payment_method, inv.mmr, inv.discount_amount, inv.discount_pct, inv.notes, inv.created_at, inv.updated_at,
               si.selling_price, si.selling_date, si.customer_id, si.vehicle_id, si.employee_id, si.store_id, (si.selling_price - inv.discount_amount) AS final_amount,
               CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name, ci.customer_address, CONCAT(ii.make_name, ' ', vi.vehicle_model) AS vehicle_name, vi.vin,
               CONCAT(e.first_name, ' ', e.last_name) AS employee_name, er.role_name AS employee_role, s.store_name, s.address AS store_address
        FROM invoice inv
        INNER JOIN selling_info si  ON inv.sell_id = si.sell_id
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN vehicle_info vi  ON si.vehicle_id = vi.id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        INNER JOIN employee e       ON si.employee_id = e.employee_id
        INNER JOIN employee_role er ON e.employee_role = er.role_id
        INNER JOIN store s          ON si.store_id = s.store_id
        WHERE inv.invoice_id = %s
        """
        return execute_fetchone_query(InvoiceSerializer.DB_NAME, query, [invoice_id])

    @staticmethod
    def fetch_by_sell_id(sell_id):
        row = execute_fetchone_query(InvoiceSerializer.DB_NAME, "SELECT invoice_id FROM invoice WHERE sell_id = %s", [sell_id])
        return InvoiceSerializer.fetch_one(row['invoice_id']) if row else None

    @staticmethod
    def create(sell_id, invoice_date, payment_status='Paid', payment_method='Cash', discount_amount=0, notes=None, due_date=None, customer_id=None, employee_id=None, store_id=None, created_at=None):
        selling_price, mmr_val = 0, 0
        row = execute_fetchone_query(InvoiceSerializer.DB_NAME, "SELECT si.customer_id, si.employee_id, si.store_id, si.selling_date, si.created_at, si.selling_price, vi.mmr FROM selling_info si INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id WHERE si.sell_id = %s", [sell_id])
        if row:
            customer_id = customer_id or row['customer_id']
            employee_id = employee_id or row['employee_id']
            store_id = store_id or row['store_id']
            invoice_date = invoice_date or row['selling_date']
            created_at = created_at or row['created_at']
            selling_price = row['selling_price']
            mmr_val = row['mmr']

        if mmr_val > selling_price:
            discount_amount = mmr_val - selling_price
            discount_pct = round(((mmr_val - selling_price) / mmr_val) * 100, 2)
        else:
            discount_amount = 0
            discount_pct = 0.00

        row_max = execute_fetchone_query(InvoiceSerializer.DB_NAME, "SELECT MAX(invoice_id) AS max_id FROM invoice")
        max_id = row_max['max_id'] if (row_max and row_max['max_id'] is not None) else 3999
        invoice_id = max_id + 1

        query = """
        INSERT INTO invoice (invoice_id, sell_id, customer_id, employee_id, store_id, invoice_date, due_date, payment_status, payment_method, mmr, discount_amount, discount_pct, notes, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_cud_query(InvoiceSerializer.DB_NAME, query, [invoice_id, sell_id, customer_id, employee_id, store_id, invoice_date, due_date, payment_status, payment_method, mmr_val, discount_amount, discount_pct, notes, created_at, created_at or None])
        return invoice_id

    @staticmethod
    def update(invoice_id, invoice_date, due_date, payment_status, payment_method, discount_amount, notes):
        row = execute_fetchone_query(InvoiceSerializer.DB_NAME, """
            SELECT i.mmr, s.selling_price
            FROM invoice i
            INNER JOIN selling_info s ON i.sell_id = s.sell_id
            WHERE i.invoice_id = %s
        """, [invoice_id])
        if row:
            mmr_val = row['mmr']
            selling_price = row['selling_price']
            if mmr_val > selling_price:
                discount_amount = mmr_val - selling_price
                discount_pct = round(((mmr_val - selling_price) / mmr_val) * 100, 2)
            else:
                discount_amount = 0
                discount_pct = 0.00
        else:
            discount_amount = 0
            discount_pct = 0.00

        query = "UPDATE invoice SET invoice_date = %s, due_date = %s, payment_status = %s, payment_method = %s, discount_amount = %s, discount_pct = %s, notes = %s, updated_at = NOW() WHERE invoice_id = %s"
        execute_cud_query(InvoiceSerializer.DB_NAME, query, [invoice_date, due_date, payment_status, payment_method, discount_amount, discount_pct, notes, invoice_id])

    @staticmethod
    def delete(invoice_id):
        execute_cud_query(InvoiceSerializer.DB_NAME, "DELETE FROM invoice WHERE invoice_id = %s", [invoice_id])

    @staticmethod
    def create_from_request(data):
        sell_id = data.get('sell_id')
        invoice_date = data.get('invoice_date')
        if not invoice_date:
            raise ValueError('invoice_date is required.')
        
        # If sell_id is not provided, we create a new sale from scratch using inventory_id
        if not sell_id:
            inventory_id = data.get('inventory_id')
            customer = data.get('customer')
            employee = data.get('employee')
            selling_price = data.get('selling_price')
            selling_date = data.get('selling_date') or invoice_date

            if not inventory_id or not customer or not employee or selling_price is None:
                raise ValueError('To create an invoice from scratch, inventory_id, customer, employee, and selling_price are required.')

            with transaction.atomic():
                # Fetch inventory details
                inv_item = inventoryserializer.fetch_one(inventory_id)
                if not inv_item:
                    raise ValueError('Selected inventory item does not exist.')
                if inv_item['status'] == 1:
                    raise ValueError('Selected inventory item is already sold.')

                # Create SellingInfo record
                sell_id = SellingInfoSerializer.create(
                    customer=customer,
                    vehicle=inv_item['vehicle'],
                    employee=employee,
                    store=inv_item['store'],
                    selling_price=selling_price,
                    selling_date=selling_date
                )

                # Link sale to inventory and mark as Sold (1)
                inventoryserializer.update(
                    inventory_id=inventory_id,
                    vehicle_id=inv_item['vehicle'],
                    store_id=inv_item['store'],
                    employee_id=inv_item['employee'],
                    status=1, # Sold
                    selling_info=sell_id
                )

        existing = InvoiceSerializer.fetch_by_sell_id(sell_id)
        if existing:
            raise ValueError(f'An invoice (#{existing["invoice_id"]}) already exists for sale #{sell_id}.')
        
        new_id = InvoiceSerializer.create(
            sell_id=sell_id,
            invoice_date=invoice_date,
            due_date=data.get('due_date') or None,
            payment_status=data.get('payment_status', 'Paid'),
            payment_method=data.get('payment_method', 'Cash'),
            discount_amount=data.get('discount_amount', 0),
            notes=data.get('notes') or None
        )
        return InvoiceSerializer.fetch_one(new_id)

    @staticmethod
    def update_from_request(invoice_id, data):
        item = InvoiceSerializer.fetch_one(invoice_id)
        if not item:
            return None
        invoice_date = data.get('invoice_date', item['invoice_date'])
        due_date = data.get('due_date', item.get('due_date')) or None
        payment_status = data.get('payment_status', item['payment_status'])
        payment_method = data.get('payment_method', item['payment_method'])
        discount_amount = data.get('discount_amount', item['discount_amount'])
        notes = data.get('notes', item.get('notes')) or None
        
        InvoiceSerializer.update(invoice_id, invoice_date, due_date, payment_status, payment_method, discount_amount, notes)
        return InvoiceSerializer.fetch_one(invoice_id)

    @staticmethod
    def delete_by_id(invoice_id):
        item = InvoiceSerializer.fetch_one(invoice_id)
        if not item:
            return False
        InvoiceSerializer.delete(invoice_id)
        return True
