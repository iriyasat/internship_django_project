
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('car_sales', '0007_employeerole_access_level_employeerole_is_manager'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employeerole',
            name='is_manager',
        ),
    ]
