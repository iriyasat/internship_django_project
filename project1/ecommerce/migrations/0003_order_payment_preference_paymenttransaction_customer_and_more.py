
import car_sales.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car_sales', '0013_populate_customer_phone_numbers'),
        ('ecommerce', '0002_order_assigned_employee_order_rejection_reason_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_preference',
            field=models.CharField(choices=[('ONLINE_CARD', 'Online Card (Upfront)'), ('STORE_PAYMENT', 'Pay Upfront at Store (Cash/Card)'), ('CASH_ON_DELIVERY', 'Cash on Delivery (COD)'), ('FINANCING', 'Financing / Bank Transfer')], default='ONLINE_CARD', max_length=30, verbose_name='Payment Preference'),
        ),
        migrations.AddField(
            model_name='paymenttransaction',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='car_sales.customer', verbose_name='Customer'),
        ),
        migrations.AddField(
            model_name='paymenttransaction',
            name='invoice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='car_sales.invoice', verbose_name='Invoice'),
        ),
        migrations.AddField(
            model_name='paymenttransaction',
            name='payment_type',
            field=models.CharField(choices=[('HOLD_DEPOSIT', 'Hold Deposit'), ('FULL_PAYMENT', 'Full Payment'), ('BALANCE_PAYMENT', 'Remaining Balance'), ('REFUND', 'Refund')], default='FULL_PAYMENT', max_length=20, verbose_name='Payment Type'),
        ),
        migrations.AddField(
            model_name='paymenttransaction',
            name='recorded_by_employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_payments', to='car_sales.employee', verbose_name='Recorded By Employee'),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('NEEDS_APPROVAL', 'Needs Approval'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('PARTIALLY_PAID', 'Partially Paid'), ('PAID', 'Paid'), ('FULFILLED', 'Fulfilled'), ('CANCELLED', 'Cancelled')], default='NEEDS_APPROVAL', max_length=20, verbose_name='Order Status'),
        ),
        migrations.AlterField(
            model_name='paymenttransaction',
            name='gateway_transaction_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name='Gateway Transaction ID'),
        ),
        migrations.AlterField(
            model_name='paymenttransaction',
            name='payment_method',
            field=models.CharField(choices=[('ONLINE_CARD', 'Online Card'), ('STORE_CARD', 'Card (at Store)'), ('STORE_CASH', 'Cash (at Store)'), ('CASH_ON_DELIVERY', 'Cash on Delivery (COD)'), ('BANK_TRANSFER', 'Bank Transfer / Wire'), ('FINANCING', 'Dealership Financing')], default='ONLINE_CARD', max_length=30, verbose_name='Payment Method'),
        ),
        migrations.CreateModel(
            name='TestDriveBooking',
            fields=[
                ('booking_id', models.AutoField(primary_key=True, serialize=False, verbose_name='Booking ID')),
                ('booking_date', models.DateField(verbose_name='Booking Date')),
                ('booking_time', models.TimeField(verbose_name='Booking Time')),
                ('status', models.CharField(choices=[('SCHEDULED', 'Scheduled'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'), ('NO_SHOW', 'No Show')], default='SCHEDULED', max_length=20, verbose_name='Status')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes')),
                ('created_at', car_sales.models.TruncatedDateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', car_sales.models.TruncatedDateTimeField(auto_now=True, verbose_name='Updated At')),
                ('assigned_employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hosted_test_drives', to='car_sales.employee', verbose_name='Assigned Staff')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_drives', to='car_sales.customer', verbose_name='Customer')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_drives', to='car_sales.store', verbose_name='Store')),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_drives', to='car_sales.vehicleinfo', verbose_name='Vehicle')),
            ],
            options={
                'verbose_name_plural': 'test drive bookings',
                'db_table': 'ecommerce_test_drive_booking',
            },
        ),
    ]
