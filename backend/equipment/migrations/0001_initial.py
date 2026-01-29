# Generated manually for EquipmentUpload model.

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='EquipmentUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('summary', models.JSONField(default=dict)),
                ('data', models.JSONField(default=list)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
