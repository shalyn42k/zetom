from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contact", "0015_adminuser_permissions_override"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactmessage",
            name="assigned_to",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_messages",
                to="contact.adminuser",
            ),
        ),
    ]
