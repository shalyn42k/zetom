
# === FILE SUMMARY ===
# Purpose: Introduce Department model and update AdminUser/ContactMessage to use department codes.
# Responsible for: Creating Department table, adjusting AdminUser level choices, and updating message fields.
# Connected to: AdminUser and ContactMessage model changes involving department references.
# Important classes/functions: Migration
# Notes: Aligns schema with multilingual department labels.
# =====================================
from django.db import migrations, models


def populate_departments_and_admins(apps, schema_editor):
    Department = apps.get_model("contact", "Department")
    AdminUser = apps.get_model("contact", "AdminUser")

    defaults = [
        ("firma1", "Firma 1", "Company 1"),
        ("firma2", "Firma 2", "Company 2"),
        ("firma3", "Firma 3", "Company 3"),
        ("inna", "Inna", "Other"),
    ]

    for code, name_pl, name_en in defaults:
        Department.objects.get_or_create(
            code=code, defaults={"name_pl": name_pl, "name_en": name_en}
        )

    for user in AdminUser.objects.all():
        current_level = getattr(user, "level", None) or AdminUser.LEVEL_ADMIN
        user.level_of_access = current_level
        user.save(update_fields=["level_of_access"])
        department_code = getattr(user, "department", None)
        if department_code:
            department = Department.objects.filter(code=department_code).first()
            if department:
                user.departments.add(department)


class Migration(migrations.Migration):

    dependencies = [
        ("contact", "0011_alter_adminuser_department"),
    ]

    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=50, unique=True)),
                ("name_pl", models.CharField(max_length=100)),
                ("name_en", models.CharField(max_length=100)),
            ],
            options={
                "ordering": ["code"],
            },
        ),
        migrations.AddField(
            model_name="adminuser",
            name="level_of_access",
            field=models.CharField(
                choices=[
                    ("level1", "level1"),
                    ("level2", "level2"),
                    ("level3", "level3"),
                ],
                default="level1",
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="adminuser",
            name="departments",
            field=models.ManyToManyField(
                blank=True, related_name="admins", to="contact.department"
            ),
        ),
        migrations.RunPython(populate_departments_and_admins, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="adminuser",
            name="department",
        ),
        migrations.RemoveField(
            model_name="adminuser",
            name="level",
        ),
        migrations.RemoveField(
            model_name="adminuser",
            name="password_ciphertext",
        ),
    ]
