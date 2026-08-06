import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car_sales', '0002_add_invoice_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='customer',
            field=models.ForeignKey(
                blank=True,
                db_column='customer_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='invoices',
                to='car_sales.customerinfo',
                verbose_name='Customer',
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='employee',
            field=models.ForeignKey(
                blank=True,
                db_column='employee_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='invoices',
                to='car_sales.employee',
                verbose_name='Employee',
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='store',
            field=models.ForeignKey(
                blank=True,
                db_column='store_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='invoices',
                to='car_sales.store',
                verbose_name='Store',
            ),
        ),
    ]
