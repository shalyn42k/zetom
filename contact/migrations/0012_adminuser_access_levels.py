from __future__ import annotations

from django.db import migrations, models


def _migrate_departments(apps, schema_editor):
    AdminUser = apps.get_model('contact', 'AdminUser')
    for user in AdminUser.objects.all():
        if getattr(user, 'department', None):
            user.departments = [user.department]
        else:
            user.departments = []
        user.save(update_fields=['departments'])


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0011_alter_adminuser_department'),
    ]

    operations = [
        migrations.RenameField(
            model_name='adminuser',
            old_name='level',
            new_name='level_of_access',
        ),
        migrations.AddField(
            model_name='adminuser',
            name='departments',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(_migrate_departments, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='adminuser',
            name='department',
        ),
        migrations.RemoveField(
            model_name='adminuser',
            name='password_ciphertext',
        ),
    ]
