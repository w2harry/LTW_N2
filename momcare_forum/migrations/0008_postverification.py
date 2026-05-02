from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def migrate_existing_verifications(apps, schema_editor):
    Post = apps.get_model('forum', 'Post')
    PostVerification = apps.get_model('forum', 'PostVerification')

    for post in Post.objects.filter(verified_by_expert=True, verified_by__isnull=False):
        reasons = (post.verification_reasons or '').strip()
        if not reasons and post.verification_reason:
            reasons = post.verification_reason

        PostVerification.objects.get_or_create(
            post_id=post.id,
            doctor_id=post.verified_by_id,
            defaults={
                'verification_reasons': reasons,
                'verification_note': post.verification_note or '',
                'verified_at': post.verified_at or timezone.now(),
            },
        )


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0007_alter_category_options_alter_otptoken_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PostVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('verification_reasons', models.TextField(blank=True, verbose_name='Danh sách lý do kiểm duyệt')),
                ('verification_note', models.TextField(blank=True, verbose_name='Ghi chú kiểm duyệt')),
                ('verified_at', models.DateTimeField(default=timezone.now, verbose_name='Thời gian kiểm duyệt')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_verifications', to=settings.AUTH_USER_MODEL, verbose_name='Bác sĩ kiểm duyệt')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verifications', to='forum.post', verbose_name='Bài viết')),
            ],
            options={
                'verbose_name': 'Lịch sử kiểm duyệt bài viết',
                'verbose_name_plural': 'Lịch sử kiểm duyệt bài viết',
                'ordering': ['-verified_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='postverification',
            constraint=models.UniqueConstraint(fields=('post', 'doctor'), name='uniq_post_doctor_verification'),
        ),
        migrations.RunPython(migrate_existing_verifications, reverse_noop),
    ]
