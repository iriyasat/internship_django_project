
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car_sales', '0005_alter_invoice_payment_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='invoice_id',
            field=models.IntegerField(primary_key=True, serialize=False, verbose_name='Invoice ID'),
        ),
    ]
