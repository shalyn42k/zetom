from django.db import migrations


NEW_DEPARTMENTS = {
    "firma1": "Elektrotechniczne",
    "firma2": "Dlugosci i Kąta",
    "firma3": "Mechaniczna",
    "inna": "inne",
}


DEPARTMENT_LABELS = {
    "Elektrotechniczne": ("Elektrotechniczne", "Electrotechnical"),
    "Dlugosci i Kąta": ("Dlugosci i Kąta", "Length and Angle"),
    "Mechaniczna": ("Mechaniczna", "Mechanical"),
    "inne": ("Inne", "Other"),
}


ALLOWED_DEPARTMENTS = {
    "Elektrotechniczne",
    "Dlugosci i Kąta",
    "Mechaniczna",
    "inne",
}


def _update_departments(apps, schema_editor):
    Department = apps.get_model("contact", "Department")
    ContactMessage = apps.get_model("contact", "ContactMessage")
    ClientChangeLog = apps.get_model("contact", "ClientChangeLog")

    for old_code, new_code in NEW_DEPARTMENTS.items():
        try:
            department = Department.objects.get(code=old_code)
        except Department.DoesNotExist:
            continue

        name_pl, name_en = DEPARTMENT_LABELS.get(new_code, (department.name_pl, department.name_en))
        department.code = new_code
        department.name_pl = name_pl
        department.name_en = name_en
        department.save(update_fields=["code", "name_pl", "name_en"])

    for code, (name_pl, name_en) in DEPARTMENT_LABELS.items():
        Department.objects.get_or_create(
            code=code,
            defaults={"name_pl": name_pl, "name_en": name_en},
        )

    for old_code, new_code in NEW_DEPARTMENTS.items():
        ContactMessage.objects.filter(company=old_code).update(company=new_code)
        ClientChangeLog.objects.filter(
            field="company", previous_value=old_code
        ).update(previous_value=new_code)
        ClientChangeLog.objects.filter(
            field="company", new_value=old_code
        ).update(new_value=new_code)

    ContactMessage.objects.exclude(company__in=ALLOWED_DEPARTMENTS).update(company="inne")
    ClientChangeLog.objects.filter(field="company").exclude(
        new_value__in=ALLOWED_DEPARTMENTS
    ).update(new_value="inne")
    ClientChangeLog.objects.filter(field="company").exclude(
        previous_value__in=ALLOWED_DEPARTMENTS
    ).update(previous_value="inne")


class Migration(migrations.Migration):
    dependencies = [
        ("contact", "0013_adminuser_last_password_reset_at"),
    ]

    operations = [
        migrations.RunPython(_update_departments, migrations.RunPython.noop),
    ]
