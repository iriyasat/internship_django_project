
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car_sales', '0008_remove_employeerole_is_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeerole',
            name='level',
            field=models.IntegerField(blank=True, null=True, verbose_name='Level'),
        ),
        migrations.AddField(
            model_name='employeerole',
            name='notes',
            field=models.TextField(blank=True, null=True, verbose_name='Notes'),
        ),
    ]
