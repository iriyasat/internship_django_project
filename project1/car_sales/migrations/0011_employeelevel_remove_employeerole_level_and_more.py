
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car_sales', '0010_remove_employeerole_access_level'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeLevel',
            fields=[
                ('level', models.IntegerField(primary_key=True, serialize=False, verbose_name='Level')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes')),
            ],
            options={
                'verbose_name_plural': 'employee levels',
                'db_table': 'employee_level',
            },
        ),
        migrations.RemoveField(
            model_name='employeerole',
            name='level',
        ),
        migrations.RemoveField(
            model_name='employeerole',
            name='notes',
        ),
        migrations.CreateModel(
            name='EmployeeHierarchy',
            fields=[
                ('employee', models.OneToOneField(db_column='employee_id', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='hierarchy', serialize=False, to='car_sales.employee', verbose_name='Employee')),
                ('role', models.ForeignKey(db_column='role_id', on_delete=django.db.models.deletion.CASCADE, related_name='role_hierarchies', to='car_sales.employeerole', verbose_name='Role')),
                ('level', models.ForeignKey(db_column='level', on_delete=django.db.models.deletion.CASCADE, related_name='hierarchies', to='car_sales.employeelevel', verbose_name='Level')),
                ('status', models.ForeignKey(db_column='status_id', on_delete=django.db.models.deletion.CASCADE, related_name='status_hierarchies', to='car_sales.employeestatus', verbose_name='Employee Status')),
                ('supervisor', models.ForeignKey(blank=True, db_column='supervisor_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor_hierarchies', to='car_sales.employee', verbose_name='Supervisor')),
                ('supervisor_role', models.ForeignKey(blank=True, db_column='supervisor_role_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor_role_hierarchies', to='car_sales.employeerole', verbose_name='Supervisor Role')),
                ('supervisor2', models.ForeignKey(blank=True, db_column='supervisor2_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor2_hierarchies', to='car_sales.employee', verbose_name='Supervisor 2')),
                ('supervisor2_role', models.ForeignKey(blank=True, db_column='supervisor2_role_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor2_role_hierarchies', to='car_sales.employeerole', verbose_name='Supervisor 2 Role')),
                ('supervisor3', models.ForeignKey(blank=True, db_column='supervisor3_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor3_hierarchies', to='car_sales.employee', verbose_name='Supervisor 3')),
                ('supervisor3_role', models.ForeignKey(blank=True, db_column='supervisor3_role_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor3_role_hierarchies', to='car_sales.employeerole', verbose_name='Supervisor 3 Role')),
                ('supervisor4', models.ForeignKey(blank=True, db_column='supervisor4_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor4_hierarchies', to='car_sales.employee', verbose_name='Supervisor 4')),
                ('supervisor4_role', models.ForeignKey(blank=True, db_column='supervisor4_role_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor4_role_hierarchies', to='car_sales.employeerole', verbose_name='Supervisor 4 Role')),
                ('supervisor5', models.ForeignKey(blank=True, db_column='supervisor5_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor5_hierarchies', to='car_sales.employee', verbose_name='Supervisor 5')),
                ('supervisor5_role', models.ForeignKey(blank=True, db_column='supervisor5_role_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor5_role_hierarchies', to='car_sales.employeerole', verbose_name='Supervisor 5 Role')),
                ('supervisor6', models.ForeignKey(blank=True, db_column='supervisor6_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor6_hierarchies', to='car_sales.employee', verbose_name='Supervisor 6')),
                ('supervisor6_role', models.ForeignKey(blank=True, db_column='supervisor6_role_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor6_role_hierarchies', to='car_sales.employeerole', verbose_name='Supervisor 6 Role')),
                ('supervisor7', models.ForeignKey(blank=True, db_column='supervisor7_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor7_hierarchies', to='car_sales.employee', verbose_name='Supervisor 7')),
                ('supervisor7_role', models.ForeignKey(blank=True, db_column='supervisor7_role_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor7_role_hierarchies', to='car_sales.employeerole', verbose_name='Supervisor 7 Role')),
                ('supervisor8', models.ForeignKey(blank=True, db_column='supervisor8_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor8_hierarchies', to='car_sales.employee', verbose_name='Supervisor 8')),
                ('supervisor8_role', models.ForeignKey(blank=True, db_column='supervisor8_role_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervisor8_role_hierarchies', to='car_sales.employeerole', verbose_name='Supervisor 8 Role')),
            ],
            options={
                'verbose_name_plural': 'employee hierarchies',
                'db_table': 'employee_hierarchy',
            },
        ),
    ]
