# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("settings", "0006_alter_sitesettings_powered_by_text_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="comment_sensitive_keywords",
            field=models.TextField(
                blank=True,
                help_text="Comments containing any of these words or phrases are rejected. One per line, or comma-separated.",
            ),
        ),
    ]
