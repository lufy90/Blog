# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("settings", "0007_sitesettings_comment_sensitive_keywords"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="block_meaningless_comments",
            field=models.BooleanField(
                default=False,
                help_text="Reject comments that look like random keys, extreme repetition, or strings with almost no letters.",
            ),
        ),
    ]
