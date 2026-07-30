import django.db.models.deletion
import car_sales.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car_sales', '0011_employeelevel_remove_employeerole_level_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Customer',
                    fields=[
                        ('customer_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Customer ID')),
                        ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                        ('password', models.CharField(max_length=255, verbose_name='Password')),
                        ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Phone')),
                        ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                        ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
                    ],
                    options={
                        'verbose_name_plural': 'customers',
                        'db_table': 'customer',
                    },
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS `customer` (
                        `customer_id` int NOT NULL AUTO_INCREMENT,
                        `email` varchar(254) NOT NULL UNIQUE,
                        `password` varchar(255) NOT NULL,
                        `phone` varchar(20) DEFAULT NULL,
                        `created_at` datetime NOT NULL,
                        `updated_at` datetime NOT NULL,
                        PRIMARY KEY (`customer_id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                    """,
                    reverse_sql="DROP TABLE IF EXISTS `customer`;"
                )
            ]
        ),
        migrations.RunSQL(
            sql="INSERT IGNORE INTO customer (customer_id, email, password, phone, created_at, updated_at) SELECT customer_id, CONCAT('customer_', customer_id, '@example.com'), 'pbkdf2_sha256$default', NULL, created_at, updated_at FROM customer_info;",
            reverse_sql=""
        ),
        migrations.AlterField(
            model_name='sellinginfo',
            name='customer',
            field=models.ForeignKey(db_column='customer_id', on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='car_sales.customer', verbose_name='Customer'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='customer',
            field=models.ForeignKey(blank=True, db_column='customer_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='car_sales.customer', verbose_name='Customer'),
        ),
        migrations.RenameField(
            model_name='customerinfo',
            old_name='customer_id',
            new_name='customer',
        ),
        migrations.AlterField(
            model_name='customerinfo',
            name='customer',
            field=models.OneToOneField(
                db_column='customer_id',
                on_delete=django.db.models.deletion.CASCADE,
                primary_key=True,
                related_name='info',
                serialize=False,
                to='car_sales.customer',
                verbose_name='Customer'
            ),
        ),
        migrations.AddField(
            model_name='customerinfo',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_pics/', verbose_name='Profile Picture'),
        ),
    ]
