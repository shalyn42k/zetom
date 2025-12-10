from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0014_update_departments_values'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminuser',
            name='permissions_override',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
