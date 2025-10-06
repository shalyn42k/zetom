from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=20)),
                ('email', models.EmailField(max_length=254)),
                ('company', models.CharField(max_length=50)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('is_read', models.BooleanField(default=False)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
