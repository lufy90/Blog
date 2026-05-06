# Generated manually for client IP tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entries', '0003_entry_view_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='creation_ip',
            field=models.CharField(blank=True, max_length=45),
        ),
        migrations.AddField(
            model_name='entry',
            name='last_edit_ip',
            field=models.CharField(blank=True, max_length=45),
        ),
        migrations.AddField(
            model_name='comment',
            name='ip_address',
            field=models.CharField(blank=True, max_length=45),
        ),
    ]
