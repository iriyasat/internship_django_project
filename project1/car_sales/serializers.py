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


class customervehiclesalesserializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(dt_from, dt_to, store_id=None, employee_id=None):
        query = """
        SELECT
            CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name,
            CONCAT(ii.make_name, ' ', vi.vehicle_model) AS vehicle_info,
            s.store_name,
            vi.mmr,
            si.selling_price,
            (si.selling_price - vi.mmr) AS mmr_vs_selling_price,
            si.selling_date
        FROM selling_info si
        INNER JOIN store s ON si.store_id = s.store_id
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
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

        query += " ORDER BY si.selling_date DESC;"

        with connections[customervehiclesalesserializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]


class customerstorespendingserializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(dt_from, dt_to, store_id=None, employee_id=None):
        query = """
        SELECT
            CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name,
            s.store_name,
            SUM(si.selling_price) AS total_spent,
            COUNT(si.sell_id) AS total_purchased
        FROM selling_info si
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN store s ON si.store_id = s.store_id
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
        GROUP BY ci.customer_id, s.store_id
        ORDER BY total_spent DESC;
        """

        with connections[customerstorespendingserializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]


class inventoryserializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None):
        query = """
        SELECT 
            i.inventory_id,
            CONCAT(ii.make_name, ' ', vi.vehicle_model) AS vehicle_name,
            s.store_name,
            CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
            CASE 
                WHEN i.status = 1 THEN 'Sold'
                WHEN i.status = 2 THEN 'Pre-order'
                WHEN i.status = 0 THEN 'Unavailable'
                WHEN i.status = 4 THEN 'Available'
                ELSE 'Unknown'
            END AS status_label,
            i.sell_id AS selling_info,
            i.status,
            i.created_at,
            i.updated_at
        FROM inventory i
        INNER JOIN vehicle_info vi ON i.vehicle_id = vi.id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        INNER JOIN store s ON i.store_id = s.store_id
        INNER JOIN employee e ON i.employee_id = e.employee_id
        WHERE 1=1
        """
        params = []
        if store_id is not None:
            query += " AND i.store_id = %s"
            params.append(store_id)
        if employee_id is not None:
            query += " AND i.employee_id = %s"
            params.append(employee_id)

        if search:
            query += """ AND (
                i.inventory_id LIKE %s OR 
                vi.vehicle_model LIKE %s OR 
                ii.make_name LIKE %s OR 
                s.store_name LIKE %s OR 
                e.first_name LIKE %s OR 
                e.last_name LIKE %s
            )"""
            search_param = f"%{search}%"
            params.extend([search_param] * 6)

        count_query = f"SELECT COUNT(*) FROM ({query}) AS temp"
        
        query += " ORDER BY i.inventory_id ASC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with connections[inventoryserializer.DB_NAME].cursor() as cursor:
            cursor.execute(count_query, params[:-2])
            total = cursor.fetchone()[0]

            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
        data = [dict(zip(columns, row)) for row in rows]
        for item in data:
            if item['created_at']:
                item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M')
            if item['updated_at']:
                item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M')
        return total, data

    @staticmethod
    def fetch_one(inventory_id):
        query = """
        SELECT 
            inventory_id, vehicle_id AS vehicle, store_id AS store, employee_id AS employee, status, sell_id AS selling_info
        FROM inventory 
        WHERE inventory_id = %s
        """
        with connections[inventoryserializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [inventory_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
        return None

    @staticmethod
    def create(vehicle_id, store_id, employee_id, status, selling_info=None):
        query = """
        INSERT INTO inventory (vehicle_id, store_id, employee_id, status, sell_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """
        with connections[inventoryserializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [vehicle_id, store_id, employee_id, status, selling_info])
            inventory_id = cursor.lastrowid
        return inventory_id

    @staticmethod
    def update(inventory_id, vehicle_id, store_id, employee_id, status, selling_info=None):
        query = """
        UPDATE inventory 
        SET vehicle_id = %s, store_id = %s, employee_id = %s, status = %s, sell_id = %s, updated_at = NOW()
        WHERE inventory_id = %s
        """
        with connections[inventoryserializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [vehicle_id, store_id, employee_id, status, selling_info, inventory_id])

    @staticmethod
    def delete(inventory_id):
        query = "DELETE FROM inventory WHERE inventory_id = %s"
        with connections[inventoryserializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [inventory_id])


def execute_raw_sql_query(db_name, select_base, count_base, table_alias, field_map, search_fields, limit, offset, search, store_id, employee_id, store_col, employee_col, filters):
    query = select_base
    count_query = count_base
    where_clauses = []
    params = []
    
    # 1. Store and Employee filters
    if store_id is not None and store_col:
        where_clauses.append(f"{store_col} = %s")
        params.append(store_id)
    if employee_id is not None and employee_col:
        where_clauses.append(f"{employee_col} = %s")
        params.append(employee_id)
        
    # 2. Arbitrary filters
    for key, val in filters.items():
        if val is not None and val != '':
            col_name = field_map.get(key, key)
            if '.' not in col_name and table_alias:
                col_name = f"{table_alias}.{col_name}"
            where_clauses.append(f"{col_name} = %s")
            params.append(val)
            
    # 3. Search
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
        
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    with connections[db_name].cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        
    data = [dict(zip(columns, row)) for row in rows]
    for item in data:
        if 'created_at' in item and item['created_at']:
            item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
        if 'updated_at' in item and item['updated_at']:
            item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
            
    return total, data


class CountrySerializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        select_base = """
        SELECT c.country_id, c.country_name, c.created_at, c.updated_at
        FROM country c
        WHERE 1=1
        """
        count_base = "SELECT COUNT(*) FROM country c WHERE 1=1"
        return execute_raw_sql_query(
            db_name=CountrySerializer.DB_NAME,
            select_base=select_base,
            count_base=count_base,
            table_alias='c',
            field_map={},
            search_fields=['country_name'],
            limit=limit,
            offset=offset,
            search=search,
            store_id=None,
            employee_id=None,
            store_col=None,
            employee_col=None,
            filters=filters
        )

    @staticmethod
    def fetch_one(country_id):
        query = """
        SELECT c.country_id, c.country_name, c.created_at, c.updated_at
        FROM country c
        WHERE c.country_id = %s
        """
        with connections[CountrySerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [country_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                item = dict(zip(columns, row))
                if item['created_at']:
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
                if item['updated_at']:
                    item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
                    return item
        return None

    @staticmethod
    def create(country_name):
        query = "INSERT INTO country (country_name, created_at, updated_at) VALUES (%s, NOW(), NOW())"
        with connections[CountrySerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [country_name])
            return cursor.lastrowid

    @staticmethod
    def update(country_id, country_name):
        query = "UPDATE country SET country_name = %s, updated_at = NOW() WHERE country_id = %s"
        with connections[CountrySerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [country_name, country_id])

    @staticmethod
    def delete(country_id):
        query = "DELETE FROM country WHERE country_id = %s"
        with connections[CountrySerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [country_id])


class CitySerializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        select_base = """
        SELECT ci.city_id, ci.city_name, ci.country_id AS country, co.country_name, ci.created_at, ci.updated_at
        FROM city ci
        INNER JOIN country co ON ci.country_id = co.country_id
        WHERE 1=1
        """
        count_base = """
        SELECT COUNT(*) 
        FROM city ci 
        INNER JOIN country co ON ci.country_id = co.country_id 
        WHERE 1=1
        """
        return execute_raw_sql_query(
            db_name=CitySerializer.DB_NAME,
            select_base=select_base,
            count_base=count_base,
            table_alias='ci',
            field_map={'country': 'country_id'},
            search_fields=['city_name', 'co.country_name'],
            limit=limit,
            offset=offset,
            search=search,
            store_id=None,
            employee_id=None,
            store_col=None,
            employee_col=None,
            filters=filters
        )

    @staticmethod
    def fetch_one(city_id):
        query = """
        SELECT ci.city_id, ci.city_name, ci.country_id AS country, co.country_name, ci.created_at, ci.updated_at
        FROM city ci
        INNER JOIN country co ON ci.country_id = co.country_id
        WHERE ci.city_id = %s
        """
        with connections[CitySerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [city_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                item = dict(zip(columns, row))
                if item['created_at']:
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
                if item['updated_at']:
                    item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
                return item
        return None

    @staticmethod
    def create(city_name, country):
        query = "INSERT INTO city (city_name, country_id, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())"
        with connections[CitySerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [city_name, country])
            return cursor.lastrowid

    @staticmethod
    def update(city_id, city_name, country):
        query = "UPDATE city SET city_name = %s, country_id = %s, updated_at = NOW() WHERE city_id = %s"
        with connections[CitySerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [city_name, country, city_id])

    @staticmethod
    def delete(city_id):
        query = "DELETE FROM city WHERE city_id = %s"
        with connections[CitySerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [city_id])


class StoreSerializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        select_base = """
        SELECT s.store_id, s.store_name, s.store_code, s.city_id AS city, s.country_id AS country, s.address,
               ci.city_name, co.country_name, s.created_at, s.updated_at
        FROM store s
        INNER JOIN city ci ON s.city_id = ci.city_id
        INNER JOIN country co ON s.country_id = co.country_id
        WHERE 1=1
        """
        count_base = """
        SELECT COUNT(*) 
        FROM store s 
        INNER JOIN city ci ON s.city_id = ci.city_id 
        INNER JOIN country co ON s.country_id = co.country_id 
        WHERE 1=1
        """
        return execute_raw_sql_query(
            db_name=StoreSerializer.DB_NAME,
            select_base=select_base,
            count_base=count_base,
            table_alias='s',
            field_map={'city': 'city_id', 'country': 'country_id'},
            search_fields=['store_name', 'store_code', 'ci.city_name', 'address'],
            limit=limit,
            offset=offset,
            search=search,
            store_id=store_id,
            employee_id=None,
            store_col='s.store_id',
            employee_col=None,
            filters=filters
        )

    @staticmethod
    def fetch_one(store_id):
        query = """
        SELECT s.store_id, s.store_name, s.store_code, s.city_id AS city, s.country_id AS country, s.address,
               ci.city_name, co.country_name, s.created_at, s.updated_at
        FROM store s
        INNER JOIN city ci ON s.city_id = ci.city_id
        INNER JOIN country co ON s.country_id = co.country_id
        WHERE s.store_id = %s
        """
        with connections[StoreSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [store_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                item = dict(zip(columns, row))
                if item['created_at']:
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
                if item['updated_at']:
                    item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
                return item
        return None

    @staticmethod
    def create(store_name, store_code, city, country, address):
        query = """
        INSERT INTO store (store_name, store_code, city_id, country_id, address, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """
        with connections[StoreSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [store_name, store_code, city, country, address])
            return cursor.lastrowid

    @staticmethod
    def update(store_id, store_name, store_code, city, country, address):
        query = """
        UPDATE store 
        SET store_name = %s, store_code = %s, city_id = %s, country_id = %s, address = %s, updated_at = NOW() 
        WHERE store_id = %s
        """
        with connections[StoreSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [store_name, store_code, city, country, address, store_id])

    @staticmethod
    def delete(store_id):
        query = "DELETE FROM store WHERE store_id = %s"
        with connections[StoreSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [store_id])


class EmployeeRoleSerializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        select_base = "SELECT er.role_id, er.role_name, er.created_at, er.updated_at FROM employee_role er WHERE 1=1"
        count_base = "SELECT COUNT(*) FROM employee_role er WHERE 1=1"
        return execute_raw_sql_query(
            db_name=EmployeeRoleSerializer.DB_NAME,
            select_base=select_base,
            count_base=count_base,
            table_alias='er',
            field_map={},
            search_fields=['role_name'],
            limit=limit,
            offset=offset,
            search=search,
            store_id=None,
            employee_id=None,
            store_col=None,
            employee_col=None,
            filters=filters
        )

    @staticmethod
    def fetch_one(role_id):
        query = "SELECT er.role_id, er.role_name, er.created_at, er.updated_at FROM employee_role er WHERE er.role_id = %s"
        with connections[EmployeeRoleSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [role_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                item = dict(zip(columns, row))
                if item['created_at']:
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
                if item['updated_at']:
                    item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
                return item
        return None

    @staticmethod
    def create(role_name):
        query = "INSERT INTO employee_role (role_name, created_at, updated_at) VALUES (%s, NOW(), NOW())"
        with connections[EmployeeRoleSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [role_name])
            return cursor.lastrowid

    @staticmethod
    def update(role_id, role_name):
        query = "UPDATE employee_role SET role_name = %s, updated_at = NOW() WHERE role_id = %s"
        with connections[EmployeeRoleSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [role_name, role_id])

    @staticmethod
    def delete(role_id):
        query = "DELETE FROM employee_role WHERE role_id = %s"
        with connections[EmployeeRoleSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [role_id])


class EmployeeStatusSerializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        select_base = "SELECT es.status_id, es.status, es.created_at, es.updated_at FROM employee_status es WHERE 1=1"
        count_base = "SELECT COUNT(*) FROM employee_status es WHERE 1=1"
        return execute_raw_sql_query(
            db_name=EmployeeStatusSerializer.DB_NAME,
            select_base=select_base,
            count_base=count_base,
            table_alias='es',
            field_map={},
            search_fields=['status'],
            limit=limit,
            offset=offset,
            search=search,
            store_id=None,
            employee_id=None,
            store_col=None,
            employee_col=None,
            filters=filters
        )

    @staticmethod
    def fetch_one(status_id):
        query = "SELECT es.status_id, es.status, es.created_at, es.updated_at FROM employee_status es WHERE es.status_id = %s"
        with connections[EmployeeStatusSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [status_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                item = dict(zip(columns, row))
                if item['created_at']:
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
                if item['updated_at']:
                    item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
                return item
        return None

    @staticmethod
    def create(status):
        query = "INSERT INTO employee_status (status, created_at, updated_at) VALUES (%s, NOW(), NOW())"
        with connections[EmployeeStatusSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [status])
            return cursor.lastrowid

    @staticmethod
    def update(status_id, status):
        query = "UPDATE employee_status SET status = %s, updated_at = NOW() WHERE status_id = %s"
        with connections[EmployeeStatusSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [status, status_id])

    @staticmethod
    def delete(status_id):
        query = "DELETE FROM employee_status WHERE status_id = %s"
        with connections[EmployeeStatusSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [status_id])


class IndustryInfoSerializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        select_base = "SELECT ii.make_id, ii.make_name, ii.created_at, ii.updated_at FROM industry_info ii WHERE 1=1"
        count_base = "SELECT COUNT(*) FROM industry_info ii WHERE 1=1"
        return execute_raw_sql_query(
            db_name=IndustryInfoSerializer.DB_NAME,
            select_base=select_base,
            count_base=count_base,
            table_alias='ii',
            field_map={},
            search_fields=['make_name'],
            limit=limit,
            offset=offset,
            search=search,
            store_id=None,
            employee_id=None,
            store_col=None,
            employee_col=None,
            filters=filters
        )

    @staticmethod
    def fetch_one(make_id):
        query = "SELECT ii.make_id, ii.make_name, ii.created_at, ii.updated_at FROM industry_info ii WHERE ii.make_id = %s"
        with connections[IndustryInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [make_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                item = dict(zip(columns, row))
                if item['created_at']:
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
                if item['updated_at']:
                    item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
                return item
        return None

    @staticmethod
    def create(make_name):
        query = "INSERT INTO industry_info (make_name, created_at, updated_at) VALUES (%s, NOW(), NOW())"
        with connections[IndustryInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [make_name])
            return cursor.lastrowid

    @staticmethod
    def update(make_id, make_name):
        query = "UPDATE industry_info SET make_name = %s, updated_at = NOW() WHERE make_id = %s"
        with connections[IndustryInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [make_name, make_id])

    @staticmethod
    def delete(make_id):
        query = "DELETE FROM industry_info WHERE make_id = %s"
        with connections[IndustryInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [make_id])


class VehicleInfoSerializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        select_base = """
        SELECT vi.id, vi.vehicle_model, vi.make_id AS make, vi.mmr, vi.trim, vi.body, vi.transmission, vi.vin, vi.state, vi.condition, vi.odometer, vi.color, vi.interior,
               ii.make_name, vi.created_at, vi.updated_at
        FROM vehicle_info vi
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        WHERE 1=1
        """
        count_base = """
        SELECT COUNT(*) 
        FROM vehicle_info vi 
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id 
        WHERE 1=1
        """
        return execute_raw_sql_query(
            db_name=VehicleInfoSerializer.DB_NAME,
            select_base=select_base,
            count_base=count_base,
            table_alias='vi',
            field_map={'make': 'make_id'},
            search_fields=['vehicle_model', 'ii.make_name', 'vin', 'color'],
            limit=limit,
            offset=offset,
            search=search,
            store_id=None,
            employee_id=None,
            store_col=None,
            employee_col=None,
            filters=filters
        )

    @staticmethod
    def fetch_one(vehicle_id):
        query = """
        SELECT vi.id, vi.vehicle_model, vi.make_id AS make, vi.mmr, vi.trim, vi.body, vi.transmission, vi.vin, vi.state, vi.condition, vi.odometer, vi.color, vi.interior,
               ii.make_name, vi.created_at, vi.updated_at
        FROM vehicle_info vi
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        WHERE vi.id = %s
        """
        with connections[VehicleInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [vehicle_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                item = dict(zip(columns, row))
                if item['created_at']:
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
                if item['updated_at']:
                    item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
                return item
        return None

    @staticmethod
    def create(vehicle_model, make, mmr, trim=None, body=None, transmission=None, vin=None, state=None, condition=None, odometer=None, color=None, interior=None):
        query = """
        INSERT INTO vehicle_info (vehicle_model, make_id, mmr, trim, body, transmission, vin, state, `condition`, odometer, color, interior, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        with connections[VehicleInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [vehicle_model, make, mmr, trim, body, transmission, vin, state, condition, odometer, color, interior])
            return cursor.lastrowid

    @staticmethod
    def update(id, vehicle_model, make, mmr, trim=None, body=None, transmission=None, vin=None, state=None, condition=None, odometer=None, color=None, interior=None):
        query = """
        UPDATE vehicle_info 
        SET vehicle_model = %s, make_id = %s, mmr = %s, trim = %s, body = %s, transmission = %s, vin = %s, state = %s, `condition` = %s, odometer = %s, color = %s, interior = %s, updated_at = NOW() 
        WHERE id = %s
        """
        with connections[VehicleInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [vehicle_model, make, mmr, trim, body, transmission, vin, state, condition, odometer, color, interior, id])

    @staticmethod
    def delete(vehicle_id):
        query = "DELETE FROM vehicle_info WHERE id = %s"
        with connections[VehicleInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [vehicle_id])


class CustomerInfoSerializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        where_clauses = ["1=1"]
        params = []
        
        if store_id is not None:
            where_clauses.append("EXISTS (SELECT 1 FROM selling_info si WHERE si.customer_id = ci.customer_id AND si.store_id = %s)")
            params.append(store_id)
            
        if employee_id is not None:
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
            search_clauses = []
            for field in ['firstname', 'lastname', 'customer_status', 'customer_address']:
                search_clauses.append(f"ci.{field} LIKE %s")
                params.append(search_param)
            where_clauses.append("(" + " OR ".join(search_clauses) + ")")
            
        where_str = " AND ".join(where_clauses)
        
        select_query = f"""
        SELECT ci.customer_id, ci.firstname, ci.lastname, ci.customer_status, ci.customer_address, ci.city_id AS city, ci.country_id AS country,
               c.city_name, co.country_name, ci.created_at, ci.updated_at
        FROM customer_info ci
        INNER JOIN city c ON ci.city_id = c.city_id
        INNER JOIN country co ON ci.country_id = co.country_id
        WHERE {where_str}
        ORDER BY ci.customer_id ASC
        LIMIT %s OFFSET %s
        """
        
        count_query = f"""
        SELECT COUNT(*)
        FROM customer_info ci
        INNER JOIN city c ON ci.city_id = c.city_id
        INNER JOIN country co ON ci.country_id = co.country_id
        WHERE {where_str}
        """
        
        with connections[CustomerInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
        params.extend([limit, offset])
        with connections[CustomerInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(select_query, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            
        data = [dict(zip(columns, row)) for row in rows]
        for item in data:
            if item['created_at']:
                item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
            if item['updated_at']:
                item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
        return total, data

    @staticmethod
    def fetch_one(customer_id):
        query = """
        SELECT ci.customer_id, ci.firstname, ci.lastname, ci.customer_status, ci.customer_address, ci.city_id AS city, ci.country_id AS country,
               c.city_name, co.country_name, ci.created_at, ci.updated_at
        FROM customer_info ci
        INNER JOIN city c ON ci.city_id = c.city_id
        INNER JOIN country co ON ci.country_id = co.country_id
        WHERE ci.customer_id = %s
        """
        with connections[CustomerInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [customer_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                item = dict(zip(columns, row))
                if item['created_at']:
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
                if item['updated_at']:
                    item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
                return item
        return None

    @staticmethod
    def create(firstname, lastname, customer_status, customer_address, city, country):
        query = """
        INSERT INTO customer_info (firstname, lastname, customer_status, customer_address, city_id, country_id, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        with connections[CustomerInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [firstname, lastname, customer_status, customer_address, city, country])
            return cursor.lastrowid

    @staticmethod
    def update(customer_id, firstname, lastname, customer_status, customer_address, city, country):
        query = """
        UPDATE customer_info 
        SET firstname = %s, lastname = %s, customer_status = %s, customer_address = %s, city_id = %s, country_id = %s, updated_at = NOW() 
        WHERE customer_id = %s
        """
        with connections[CustomerInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [firstname, lastname, customer_status, customer_address, city, country, customer_id])

    @staticmethod
    def delete(customer_id):
        query = "DELETE FROM customer_info WHERE customer_id = %s"
        with connections[CustomerInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [customer_id])


class SellingInfoSerializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        where_clauses = ["1=1"]
        params = []
        
        if store_id is not None:
            where_clauses.append("si.store_id = %s")
            params.append(store_id)
        if employee_id is not None:
            where_clauses.append("si.employee_id = %s")
            params.append(employee_id)
            
        field_map = {
            'customer': 'si.customer_id',
            'vehicle': 'si.vehicle_id',
            'employee': 'si.employee_id',
            'store': 'si.store_id',
            'selling_date': 'si.selling_date'
        }
        
        for key, val in filters.items():
            if val is not None and val != '':
                col = field_map.get(key, f"si.{key}")
                where_clauses.append(f"{col} = %s")
                params.append(val)
                
        if search:
            search_param = f"%{search}%"
            where_clauses.append("""(
                ci.firstname LIKE %s OR 
                ci.lastname LIKE %s OR 
                vi.vehicle_model LIKE %s OR 
                ii.make_name LIKE %s
            )""")
            params.extend([search_param] * 4)
            
        where_str = " AND ".join(where_clauses)
        
        select_query = f"""
        SELECT si.sell_id, si.customer_id AS customer, si.vehicle_id AS vehicle, si.employee_id AS employee, si.store_id AS store, si.selling_price, si.selling_date,
               CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name,
               CONCAT(ii.make_name, ' ', vi.vehicle_model) AS vehicle_name,
               CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
               s.store_name, si.created_at, si.updated_at
        FROM selling_info si
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        INNER JOIN employee e ON si.employee_id = e.employee_id
        INNER JOIN store s ON si.store_id = s.store_id
        WHERE {where_str}
        ORDER BY si.sell_id ASC
        LIMIT %s OFFSET %s
        """
        
        count_query = f"""
        SELECT COUNT(*)
        FROM selling_info si
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
            
        params.extend([limit, offset])
        with connections[SellingInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(select_query, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            
        data = [dict(zip(columns, row)) for row in rows]
        for item in data:
            if item['selling_date']:
                item['selling_date'] = item['selling_date'].strftime('%Y-%m-%d') if not isinstance(item['selling_date'], str) else item['selling_date']
            if item['created_at']:
                item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
            if item['updated_at']:
                item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
        return total, data

    @staticmethod
    def fetch_one(sell_id):
        query = """
        SELECT si.sell_id, si.customer_id AS customer, si.vehicle_id AS vehicle, si.employee_id AS employee, si.store_id AS store, si.selling_price, si.selling_date,
               CONCAT(ci.firstname, ' ', ci.lastname) AS customer_name,
               CONCAT(ii.make_name, ' ', vi.vehicle_model) AS vehicle_name,
               CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
               s.store_name, si.created_at, si.updated_at
        FROM selling_info si
        INNER JOIN customer_info ci ON si.customer_id = ci.customer_id
        INNER JOIN vehicle_info vi ON si.vehicle_id = vi.id
        INNER JOIN industry_info ii ON vi.make_id = ii.make_id
        INNER JOIN employee e ON si.employee_id = e.employee_id
        INNER JOIN store s ON si.store_id = s.store_id
        WHERE si.sell_id = %s
        """
        with connections[SellingInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [sell_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                item = dict(zip(columns, row))
                if item['selling_date']:
                    item['selling_date'] = item['selling_date'].strftime('%Y-%m-%d') if not isinstance(item['selling_date'], str) else item['selling_date']
                if item['created_at']:
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
                if item['updated_at']:
                    item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
                return item
        return None

    @staticmethod
    def create(customer, vehicle, employee, store, selling_price, selling_date):
        query = """
        INSERT INTO selling_info (customer_id, vehicle_id, employee_id, store_id, selling_price, selling_date, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        with connections[SellingInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [customer, vehicle, employee, store, selling_price, selling_date])
            return cursor.lastrowid

    @staticmethod
    def update(sell_id, customer, vehicle, employee, store, selling_price, selling_date):
        query = """
        UPDATE selling_info 
        SET customer_id = %s, vehicle_id = %s, employee_id = %s, store_id = %s, selling_price = %s, selling_date = %s, updated_at = NOW() 
        WHERE sell_id = %s
        """
        with connections[SellingInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [customer, vehicle, employee, store, selling_price, selling_date, sell_id])

    @staticmethod
    def delete(sell_id):
        query = "DELETE FROM selling_info WHERE sell_id = %s"
        with connections[SellingInfoSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [sell_id])


class EmployeeBudgetSerializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        where_clauses = ["1=1"]
        params = []
        
        if store_id is not None:
            where_clauses.append("eb.store_id = %s")
            params.append(store_id)
        if employee_id is not None:
            where_clauses.append("eb.employee_id = %s")
            params.append(employee_id)
            
        field_map = {
            'employee': 'eb.employee_id',
            'store': 'eb.store_id',
            'budget_year': 'eb.budget_year',
            'budget_month': 'eb.budget_month'
        }
        
        for key, val in filters.items():
            if val is not None and val != '':
                col = field_map.get(key, f"eb.{key}")
                where_clauses.append(f"{col} = %s")
                params.append(val)
                
        if search:
            search_param = f"%{search}%"
            where_clauses.append("(e.first_name LIKE %s OR e.last_name LIKE %s OR s.store_name LIKE %s OR eb.budget_year LIKE %s)")
            params.extend([search_param] * 4)
            
        where_str = " AND ".join(where_clauses)
        
        select_query = f"""
        SELECT eb.id, eb.employee_id AS employee, eb.budget_year, eb.budget_month, eb.store_id AS store, eb.budget_qty, eb.budget_amount,
               CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
               s.store_name, eb.created_at, eb.updated_at
        FROM employee_budget eb
        INNER JOIN employee e ON eb.employee_id = e.employee_id
        INNER JOIN store s ON eb.store_id = s.store_id
        WHERE {where_str}
        ORDER BY eb.id ASC
        LIMIT %s OFFSET %s
        """
        
        count_query = f"""
        SELECT COUNT(*)
        FROM employee_budget eb
        INNER JOIN employee e ON eb.employee_id = e.employee_id
        INNER JOIN store s ON eb.store_id = s.store_id
        WHERE {where_str}
        """
        
        with connections[EmployeeBudgetSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
        params.extend([limit, offset])
        with connections[EmployeeBudgetSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(select_query, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            
        data = [dict(zip(columns, row)) for row in rows]
        for item in data:
            if item['created_at']:
                item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
            if item['updated_at']:
                item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
        return total, data

    @staticmethod
    def fetch_one(budget_id):
        query = """
        SELECT eb.id, eb.employee_id AS employee, eb.budget_year, eb.budget_month, eb.store_id AS store, eb.budget_qty, eb.budget_amount,
               CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
               s.store_name, eb.created_at, eb.updated_at
        FROM employee_budget eb
        INNER JOIN employee e ON eb.employee_id = e.employee_id
        INNER JOIN store s ON eb.store_id = s.store_id
        WHERE eb.id = %s
        """
        with connections[EmployeeBudgetSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [budget_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                item = dict(zip(columns, row))
                if item['created_at']:
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
                if item['updated_at']:
                    item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
                return item
        return None

    @staticmethod
    def create(employee, budget_year, budget_month, store, budget_qty, budget_amount):
        query = """
        INSERT INTO employee_budget (employee_id, budget_year, budget_month, store_id, budget_qty, budget_amount, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        with connections[EmployeeBudgetSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [employee, budget_year, budget_month, store, budget_qty, budget_amount])
            return cursor.lastrowid

    @staticmethod
    def update(id, employee, budget_year, budget_month, store, budget_qty, budget_amount):
        query = """
        UPDATE employee_budget 
        SET employee_id = %s, budget_year = %s, budget_month = %s, store_id = %s, budget_qty = %s, budget_amount = %s, updated_at = NOW() 
        WHERE id = %s
        """
        with connections[EmployeeBudgetSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [employee, budget_year, budget_month, store, budget_qty, budget_amount, id])

    @staticmethod
    def delete(budget_id):
        query = "DELETE FROM employee_budget WHERE id = %s"
        with connections[EmployeeBudgetSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [budget_id])


class EmployeeSerializer:
    DB_NAME = 'default'

    @staticmethod
    def fetch(limit=25, offset=0, search='', store_id=None, employee_id=None, **filters):
        where_clauses = ["1=1"]
        params = []
        
        if store_id is not None:
            where_clauses.append("e.store_id = %s")
            params.append(store_id)
        if employee_id is not None:
            where_clauses.append("e.employee_id = %s")
            params.append(employee_id)
            
        field_map = {
            'employee_role': 'e.employee_role',
            'status': 'e.status',
            'store': 'e.store_id',
            'city': 'e.city_id',
            'country': 'e.country_id'
        }
        
        for key, val in filters.items():
            if val is not None and val != '':
                col = field_map.get(key, f"e.{key}")
                where_clauses.append(f"{col} = %s")
                params.append(val)
                
        if search:
            search_param = f"%{search}%"
            where_clauses.append("(e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_addr LIKE %s)")
            params.extend([search_param] * 3)
            
        where_str = " AND ".join(where_clauses)
        
        select_query = f"""
        SELECT e.employee_id, e.first_name, e.last_name, e.date_of_joining, e.employee_addr,
               e.employee_role, e.status, e.store_id AS store, e.city_id AS city, e.country_id AS country,
               er.role_name, es.status AS status_name, s.store_name, ci.city_name, co.country_name,
               e.created_at, e.updated_at
        FROM employee e
        INNER JOIN employee_role er ON e.employee_role = er.role_id
        INNER JOIN employee_status es ON e.status = es.status_id
        INNER JOIN store s ON e.store_id = s.store_id
        INNER JOIN city ci ON e.city_id = ci.city_id
        INNER JOIN country co ON e.country_id = co.country_id
        WHERE {where_str}
        ORDER BY e.employee_id ASC
        LIMIT %s OFFSET %s
        """
        
        count_query = f"""
        SELECT COUNT(*)
        FROM employee e
        INNER JOIN employee_role er ON e.employee_role = er.role_id
        INNER JOIN employee_status es ON e.status = es.status_id
        INNER JOIN store s ON e.store_id = s.store_id
        INNER JOIN city ci ON e.city_id = ci.city_id
        INNER JOIN country co ON e.country_id = co.country_id
        WHERE {where_str}
        """
        
        with connections[EmployeeSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
        params.extend([limit, offset])
        with connections[EmployeeSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(select_query, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            
        data = [dict(zip(columns, row)) for row in rows]
        for item in data:
            if item['date_of_joining']:
                item['date_of_joining'] = item['date_of_joining'].strftime('%Y-%m-%d') if not isinstance(item['date_of_joining'], str) else item['date_of_joining']
            if item['created_at']:
                item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
            if item['updated_at']:
                item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
        return total, data

    @staticmethod
    def fetch_one(employee_id):
        query = """
        SELECT e.employee_id, e.first_name, e.last_name, e.date_of_joining, e.employee_addr,
               e.employee_role, e.status, e.store_id AS store, e.city_id AS city, e.country_id AS country,
               er.role_name, es.status AS status_name, s.store_name, ci.city_name, co.country_name,
               e.created_at, e.updated_at
        FROM employee e
        INNER JOIN employee_role er ON e.employee_role = er.role_id
        INNER JOIN employee_status es ON e.status = es.status_id
        INNER JOIN store s ON e.store_id = s.store_id
        INNER JOIN city ci ON e.city_id = ci.city_id
        INNER JOIN country co ON e.country_id = co.country_id
        WHERE e.employee_id = %s
        """
        with connections[EmployeeSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [employee_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                item = dict(zip(columns, row))
                if item['date_of_joining']:
                    item['date_of_joining'] = item['date_of_joining'].strftime('%Y-%m-%d') if not isinstance(item['date_of_joining'], str) else item['date_of_joining']
                if item['created_at']:
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['created_at'], str) else item['created_at']
                if item['updated_at']:
                    item['updated_at'] = item['updated_at'].strftime('%Y-%m-%d %H:%M') if not isinstance(item['updated_at'], str) else item['updated_at']
                return item
        return None

    @staticmethod
    def create(first_name, last_name, date_of_joining, employee_addr, employee_role, status, store, city, country, password=None):
        if not password:
            password = 'CAr$@lse2014'
        query = """
        INSERT INTO employee (first_name, last_name, date_of_joining, employee_addr, employee_role, status, store_id, city_id, country_id, password, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        with connections[EmployeeSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [first_name, last_name, date_of_joining, employee_addr, employee_role, status, store, city, country, password])
            return cursor.lastrowid

    @staticmethod
    def update(employee_id, first_name, last_name, date_of_joining, employee_addr, employee_role, status, store, city, country, password=None):
        if password:
            query = """
            UPDATE employee 
            SET first_name = %s, last_name = %s, date_of_joining = %s, employee_addr = %s, employee_role = %s, status = %s, store_id = %s, city_id = %s, country_id = %s, password = %s, updated_at = NOW() 
            WHERE employee_id = %s
            """
            params = [first_name, last_name, date_of_joining, employee_addr, employee_role, status, store, city, country, password, employee_id]
        else:
            query = """
            UPDATE employee 
            SET first_name = %s, last_name = %s, date_of_joining = %s, employee_addr = %s, employee_role = %s, status = %s, store_id = %s, city_id = %s, country_id = %s, updated_at = NOW() 
            WHERE employee_id = %s
            """
            params = [first_name, last_name, date_of_joining, employee_addr, employee_role, status, store, city, country, employee_id]
        with connections[EmployeeSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, params)

    @staticmethod
    def delete(employee_id):
        query = "DELETE FROM employee WHERE employee_id = %s"
        with connections[EmployeeSerializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [employee_id])


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
        SELECT 
            si.employee_id,
            e.first_name,
            e.last_name, 
            s.store_id,
            s.store_name,
            SUM(si.selling_price) AS sell_value,
            eb.budget_amount as budget
        FROM selling_info si 
        LEFT JOIN employee e on si.employee_id=e.employee_id 
        INNER JOIN employee_budget eb ON si.employee_id=eb.employee_id 
        LEFT JOIN store s on eb.store_id=s.store_id
        WHERE eb.budget_year = %s 
          and eb.budget_month = %s 
          AND si.selling_date BETWEEN %s AND %s 
        GROUP BY si.employee_id, e.first_name, e.last_name, s.store_id, s.store_name, eb.budget_amount
        ORDER BY si.employee_id ASC;
        """
        
        with connections[budgetvssalesserializer.DB_NAME].cursor() as cursor:
            cursor.execute(query, [year_val, month_val, dt_from, dt_to])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            
        data = [dict(zip(columns, row)) for row in rows]
        
        # Calculate differences and achievement using Python if/else logic
        for item in data:
            sell_value = float(item['sell_value']) if item['sell_value'] is not None else 0.0
            budget = float(item['budget']) if item['budget'] is not None else 0.0
            
            item['sell_value'] = sell_value
            item['budget'] = budget
            item['difference'] = sell_value - budget
            
            if budget > 0:
                item['achievement'] = round((sell_value / budget) * 100, 2)
            else:
                item['achievement'] = 0.00
                
        return data
