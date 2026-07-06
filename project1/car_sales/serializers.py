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


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'

class CitySerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.country_name', read_only=True)
    class Meta:
        model = City
        fields = '__all__'

class StoreSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.city_name', read_only=True)
    country_name = serializers.CharField(source='country.country_name', read_only=True)
    class Meta:
        model = Store
        fields = '__all__'

class EmployeeRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeRole
        fields = '__all__'

class EmployeeStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeStatus
        fields = '__all__'

class IndustryInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustryInfo
        fields = '__all__'

class VehicleInfoSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.make_name', read_only=True)
    class Meta:
        model = VehicleInfo
        fields = '__all__'

class CustomerInfoSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.city_name', read_only=True)
    country_name = serializers.CharField(source='country.country_name', read_only=True)
    class Meta:
        model = CustomerInfo
        fields = '__all__'

class SellingInfoSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    vehicle_name = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    store_name = serializers.CharField(source='store.store_name', read_only=True)

    class Meta:
        model = SellingInfo
        fields = '__all__'

    def get_customer_name(self, obj):
        return f"{obj.customer.firstname} {obj.customer.lastname}" if obj.customer else 'N/A'

    def get_vehicle_name(self, obj):
        return f"{obj.vehicle.make.make_name} {obj.vehicle.vehicle_model}" if obj.vehicle and obj.vehicle.make else 'N/A'

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}" if obj.employee else 'N/A'

class EmployeeBudgetSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    store_name = serializers.CharField(source='store.store_name', read_only=True)

    class Meta:
        model = EmployeeBudget
        fields = '__all__'

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}" if obj.employee else 'N/A'


class EmployeeSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='employee_role.role_name', read_only=True)
    status_name = serializers.CharField(source='status.status', read_only=True)
    store_name = serializers.CharField(source='store.store_name', read_only=True)
    city_name = serializers.CharField(source='city.city_name', read_only=True)
    country_name = serializers.CharField(source='country.country_name', read_only=True)

    class Meta:
        model = Employee
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}
        }
