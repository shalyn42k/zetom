from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contact", "0008_adminuser"),
    ]

    operations = [
        migrations.AddField(
            model_name="adminuser",
            name="department",
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
