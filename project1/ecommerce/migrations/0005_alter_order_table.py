
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0004_remove_order_order_number'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='order',
            table='order',
        ),
    ]
