
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0006_alter_paymenttransaction_table'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='cart',
            table='cart',
        ),
        migrations.AlterModelTable(
            name='cartitem',
            table='cart_item',
        ),
        migrations.AlterModelTable(
            name='testdrivebooking',
            table='test_drive_booking',
        ),
        migrations.AlterModelTable(
            name='wishlist',
            table='wishlist',
        ),
    ]
