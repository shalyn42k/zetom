from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0009_adminuser_department'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminuser',
            name='password_ciphertext',
            field=models.TextField(blank=True),
        ),
    ]
