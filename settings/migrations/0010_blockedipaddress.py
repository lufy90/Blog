# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("settings", "0009_sitesettings_meaningless_rate_limit"),
    ]

    operations = [
        migrations.CreateModel(
            name="BlockedIPAddress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ip_address", models.CharField(max_length=45, unique=True)),
                ("note", models.CharField(blank=True, max_length=200)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Blocked IP address",
                "verbose_name_plural": "Blocked IP addresses",
                "ordering": ["-created_on"],
            },
        ),
    ]
