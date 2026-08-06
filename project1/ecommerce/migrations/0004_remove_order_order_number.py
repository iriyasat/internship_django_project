
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0003_order_payment_preference_paymenttransaction_customer_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='order_number',
        ),
    ]
