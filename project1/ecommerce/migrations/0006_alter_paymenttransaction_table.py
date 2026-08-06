
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0005_alter_order_table'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='paymenttransaction',
            table='payment',
        ),
    ]
