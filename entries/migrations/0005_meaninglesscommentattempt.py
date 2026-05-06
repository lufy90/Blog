# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entries', '0004_entry_comment_client_ip'),
    ]

    operations = [
        migrations.CreateModel(
            name='MeaninglessCommentAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('ip_address', models.CharField(blank=True, max_length=45)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                (
                    'entry',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='meaningless_attempts',
                        to='entries.entry',
                    ),
                ),
                (
                    'parent_comment',
                    models.ForeignKey(
                        blank=True,
                        help_text='Set when the attempt was a reply to this comment.',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='meaningless_reply_attempts',
                        to='entries.comment',
                    ),
                ),
            ],
            options={
                'ordering': ['-created_on'],
            },
        ),
        migrations.AddIndex(
            model_name='meaninglesscommentattempt',
            index=models.Index(fields=['ip_address', 'created_on'], name='encm_ip_created'),
        ),
        migrations.AddIndex(
            model_name='meaninglesscommentattempt',
            index=models.Index(fields=['created_on'], name='encm_created'),
        ),
    ]
