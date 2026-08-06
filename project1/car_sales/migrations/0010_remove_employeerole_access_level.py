
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('car_sales', '0009_employeerole_level_employeerole_notes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employeerole',
            name='access_level',
        ),
    ]
