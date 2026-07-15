from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car_sales', '0003_invoice_add_party_fks'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='mmr',
            field=models.IntegerField(default=0, verbose_name='MMR Price'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='discount_pct',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=5,
                default=0.00,
                verbose_name='Discount %',
            ),
        ),
    ]
