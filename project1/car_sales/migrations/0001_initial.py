
import car_sales.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('country_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Country ID')),
                ('country_name', models.CharField(max_length=100, unique=True, verbose_name='Country Name')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name_plural': 'countries',
                'db_table': 'country',
            },
        ),
        migrations.CreateModel(
            name='EmployeeRole',
            fields=[
                ('role_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Role ID')),
                ('role_name', models.CharField(max_length=100, unique=True, verbose_name='Role Name')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'db_table': 'employee_role',
            },
        ),
        migrations.CreateModel(
            name='EmployeeStatus',
            fields=[
                ('status_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Status ID')),
                ('status', models.CharField(max_length=50, unique=True, verbose_name='Status Name')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name_plural': 'employee statuses',
                'db_table': 'employee_status',
            },
        ),
        migrations.CreateModel(
            name='IndustryInfo',
            fields=[
                ('make_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Make ID')),
                ('make_name', models.CharField(max_length=100, unique=True, verbose_name='Make Name')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name_plural': 'industry info',
                'db_table': 'industry_info',
            },
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('city_id', models.AutoField(primary_key=True, serialize=False, verbose_name='City ID')),
                ('city_name', models.CharField(max_length=100, verbose_name='City Name')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
                ('country', models.ForeignKey(db_column='country_id', on_delete=django.db.models.deletion.CASCADE, related_name='cities', to='car_sales.country', verbose_name='Country')),
            ],
            options={
                'verbose_name_plural': 'cities',
                'db_table': 'city',
            },
        ),
        migrations.CreateModel(
            name='CustomerInfo',
            fields=[
                ('customer_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Customer ID')),
                ('firstname', models.CharField(max_length=100, verbose_name='First Name')),
                ('lastname', models.CharField(max_length=100, verbose_name='Last Name')),
                ('customer_status', models.CharField(max_length=50, verbose_name='Customer Status')),
                ('customer_address', models.CharField(max_length=255, verbose_name='Customer Address')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
                ('city', models.ForeignKey(db_column='city_id', on_delete=django.db.models.deletion.CASCADE, related_name='customers', to='car_sales.city', verbose_name='City')),
                ('country', models.ForeignKey(db_column='country_id', on_delete=django.db.models.deletion.CASCADE, related_name='customers', to='car_sales.country', verbose_name='Country')),
            ],
            options={
                'verbose_name_plural': 'customer info',
                'db_table': 'customer_info',
            },
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('employee_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Employee ID')),
                ('first_name', models.CharField(max_length=100, verbose_name='First Name')),
                ('last_name', models.CharField(max_length=100, verbose_name='Last Name')),
                ('date_of_joining', models.DateField(verbose_name='Date of Joining')),
                ('employee_addr', models.CharField(max_length=255, verbose_name='Employee Address')),
                ('password', models.CharField(default='CAr$@lse2014', max_length=25, verbose_name='Password')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
                ('city', models.ForeignKey(db_column='city_id', on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='car_sales.city', verbose_name='City')),
                ('country', models.ForeignKey(db_column='country_id', on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='car_sales.country', verbose_name='Country')),
                ('employee_role', models.ForeignKey(db_column='employee_role', on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='car_sales.employeerole', verbose_name='Employee Role')),
                ('status', models.ForeignKey(db_column='status', on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='car_sales.employeestatus', verbose_name='Employee Status')),
            ],
            options={
                'db_table': 'employee',
            },
        ),
        migrations.CreateModel(
            name='SellingInfo',
            fields=[
                ('sell_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Sell ID')),
                ('selling_price', models.IntegerField(verbose_name='Selling Price')),
                ('selling_date', models.DateField(db_index=True, verbose_name='Selling Date')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
                ('customer', models.ForeignKey(db_column='customer_id', on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='car_sales.customerinfo', verbose_name='Customer')),
                ('employee', models.ForeignKey(db_column='employee_id', on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='car_sales.employee', verbose_name='Employee')),
            ],
            options={
                'verbose_name_plural': 'selling info',
                'db_table': 'selling_info',
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('invoice_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Invoice ID')),
                ('invoice_date', models.DateField(verbose_name='Invoice Date')),
                ('due_date', models.DateField(blank=True, null=True, verbose_name='Due Date')),
                ('payment_status', models.CharField(choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Pending', 'Pending'), ('Overdue', 'Overdue')], default='Unpaid', max_length=20, verbose_name='Payment Status')),
                ('payment_method', models.CharField(choices=[('Cash', 'Cash'), ('Card', 'Card'), ('Bank Transfer', 'Bank Transfer'), ('Financing', 'Financing')], default='Cash', max_length=20, verbose_name='Payment Method')),
                ('discount_amount', models.IntegerField(default=0, verbose_name='Discount Amount')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
                ('selling_info', models.OneToOneField(db_column='sell_id', on_delete=django.db.models.deletion.CASCADE, related_name='invoice', to='car_sales.sellinginfo', verbose_name='Selling Info')),
            ],
            options={
                'verbose_name_plural': 'invoices',
                'db_table': 'invoice',
            },
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('store_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Store ID')),
                ('store_name', models.CharField(max_length=150, verbose_name='Store Name')),
                ('store_code', models.CharField(max_length=20, unique=True, verbose_name='Store Code')),
                ('address', models.CharField(max_length=255, verbose_name='Address')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
                ('city', models.ForeignKey(db_column='city_id', on_delete=django.db.models.deletion.CASCADE, related_name='stores', to='car_sales.city', verbose_name='City')),
                ('country', models.ForeignKey(db_column='country_id', on_delete=django.db.models.deletion.CASCADE, related_name='stores', to='car_sales.country', verbose_name='Country')),
            ],
            options={
                'db_table': 'store',
            },
        ),
        migrations.AddField(
            model_name='sellinginfo',
            name='store',
            field=models.ForeignKey(db_column='store_id', on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='car_sales.store', verbose_name='Store'),
        ),
        migrations.AddField(
            model_name='employee',
            name='store',
            field=models.ForeignKey(db_column='store_id', on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='car_sales.store', verbose_name='Store'),
        ),
        migrations.CreateModel(
            name='VehicleInfo',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='Vehicle ID')),
                ('vehicle_model', models.CharField(max_length=150, verbose_name='Vehicle Model')),
                ('mmr', models.IntegerField(verbose_name='MMR (Manheim Market Report)')),
                ('trim', models.CharField(blank=True, max_length=100, null=True, verbose_name='Trim')),
                ('body', models.CharField(blank=True, max_length=100, null=True, verbose_name='Body')),
                ('transmission', models.CharField(blank=True, max_length=50, null=True, verbose_name='Transmission')),
                ('vin', models.CharField(max_length=20, unique=True, verbose_name='VIN')),
                ('state', models.CharField(blank=True, max_length=10, null=True, verbose_name='State')),
                ('condition', models.IntegerField(blank=True, null=True, verbose_name='Condition')),
                ('odometer', models.IntegerField(blank=True, null=True, verbose_name='Odometer')),
                ('color', models.CharField(blank=True, max_length=50, null=True, verbose_name='Color')),
                ('interior', models.CharField(blank=True, max_length=50, null=True, verbose_name='Interior')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
                ('make', models.ForeignKey(db_column='make_id', on_delete=django.db.models.deletion.CASCADE, related_name='vehicles', to='car_sales.industryinfo', verbose_name='Make')),
            ],
            options={
                'verbose_name_plural': 'vehicle info',
                'db_table': 'vehicle_info',
            },
        ),
        migrations.AddField(
            model_name='sellinginfo',
            name='vehicle',
            field=models.ForeignKey(db_column='vehicle_id', on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='car_sales.vehicleinfo', verbose_name='Vehicle'),
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('inventory_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Inventory ID')),
                ('status', models.IntegerField(choices=[(1, 'Sold'), (2, 'Pre-order'), (0, 'Unavailable'), (4, 'Available')], default=4, verbose_name='Status')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
                ('employee', models.ForeignKey(db_column='employee_id', on_delete=django.db.models.deletion.CASCADE, related_name='inventory_items', to='car_sales.employee', verbose_name='Employee')),
                ('selling_info', models.OneToOneField(blank=True, db_column='sell_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventory_item', to='car_sales.sellinginfo', verbose_name='Selling Info')),
                ('store', models.ForeignKey(db_column='store_id', on_delete=django.db.models.deletion.CASCADE, related_name='inventory_items', to='car_sales.store', verbose_name='Store')),
                ('vehicle', models.OneToOneField(db_column='vehicle_id', on_delete=django.db.models.deletion.CASCADE, related_name='inventory', to='car_sales.vehicleinfo', verbose_name='Vehicle')),
            ],
            options={
                'verbose_name_plural': 'inventories',
                'db_table': 'inventory',
            },
        ),
        migrations.CreateModel(
            name='EmployeeBudget',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='Budget ID')),
                ('budget_year', models.IntegerField(verbose_name='Budget Year')),
                ('budget_month', models.IntegerField(verbose_name='Budget Month')),
                ('budget_qty', models.IntegerField(verbose_name='Budget Quantity')),
                ('budget_amount', models.IntegerField(verbose_name='Budget Amount')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
                ('employee', models.ForeignKey(db_column='employee_id', on_delete=django.db.models.deletion.CASCADE, related_name='budgets', to='car_sales.employee', verbose_name='Employee')),
                ('store', models.ForeignKey(db_column='store_id', on_delete=django.db.models.deletion.CASCADE, related_name='budgets', to='car_sales.store', verbose_name='Store')),
            ],
            options={
                'db_table': 'employee_budget',
                'unique_together': {('employee', 'budget_year', 'budget_month', 'store')},
            },
        ),
        migrations.AddIndex(
            model_name='vehicleinfo',
            index=models.Index(fields=['make'], name='vehicle_inf_make_id_c0b227_idx'),
        ),
    ]
