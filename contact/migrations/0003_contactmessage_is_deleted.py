from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contact", "0002_replace_is_read_with_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactmessage",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
