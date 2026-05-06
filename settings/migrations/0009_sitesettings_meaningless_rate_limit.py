# Generated manually

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("settings", "0008_sitesettings_block_meaningless_comments"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="meaningless_attempt_retention_days",
            field=models.PositiveIntegerField(
                default=30,
                help_text="Delete stored meaningless attempt logs older than this many days (also runs when a meaningless comment is checked).",
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="meaningless_rate_limit_max_attempts",
            field=models.PositiveIntegerField(
                default=10,
                help_text="Max meaningless comment attempts logged per IP within the window before further meaningless posts are blocked.",
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="meaningless_rate_limit_window_minutes",
            field=models.PositiveIntegerField(
                default=60,
                help_text="Sliding window (minutes) for counting meaningless attempts per IP.",
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
    ]
