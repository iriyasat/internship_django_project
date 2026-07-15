import car_sales.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car_sales', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('invoice_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Invoice ID')),
                ('selling_info', models.OneToOneField(
                    db_column='sell_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='invoice',
                    to='car_sales.sellinginfo',
                    verbose_name='Selling Info'
                )),
                ('invoice_date', models.DateField(verbose_name='Invoice Date')),
                ('due_date', models.DateField(blank=True, null=True, verbose_name='Due Date')),
                ('payment_status', models.CharField(
                    choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Pending', 'Pending'), ('Overdue', 'Overdue')],
                    default='Unpaid',
                    max_length=20,
                    verbose_name='Payment Status'
                )),
                ('payment_method', models.CharField(
                    choices=[('Cash', 'Cash'), ('Card', 'Card'), ('Bank Transfer', 'Bank Transfer'), ('Financing', 'Financing')],
                    default='Cash',
                    max_length=20,
                    verbose_name='Payment Method'
                )),
                ('discount_amount', models.IntegerField(default=0, verbose_name='Discount Amount')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name_plural': 'invoices',
                'db_table': 'invoice',
            },
        ),
    ]
