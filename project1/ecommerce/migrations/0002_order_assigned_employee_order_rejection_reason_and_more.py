
import car_sales.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car_sales', '0013_populate_customer_phone_numbers'),
        ('ecommerce', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='assigned_employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_orders', to='car_sales.employee', verbose_name='Assigned Store Employee'),
        ),
        migrations.AddField(
            model_name='order',
            name='rejection_reason',
            field=models.TextField(blank=True, null=True, verbose_name='Rejection Reason'),
        ),
        migrations.AddField(
            model_name='order',
            name='reviewed_at',
            field=car_sales.models.TruncatedDateTimeField(blank=True, null=True, verbose_name='Reviewed At'),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('NEEDS_APPROVAL', 'Needs Approval'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('PAID', 'Paid'), ('DEPOSIT_PAID', 'Deposit Paid'), ('FULFILLED', 'Fulfilled'), ('CANCELLED', 'Cancelled')], default='NEEDS_APPROVAL', max_length=20, verbose_name='Order Status'),
        ),
    ]
