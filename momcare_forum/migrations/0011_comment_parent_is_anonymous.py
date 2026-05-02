# Generated manually to support comment threads and anonymous comments.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0010_postverification_custom_reasons'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='is_anonymous',
            field=models.BooleanField(default=False, verbose_name='Bình luận ẩn danh'),
        ),
        migrations.AddField(
            model_name='comment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='forum.comment', verbose_name='Bình luận cha'),
        ),
    ]
