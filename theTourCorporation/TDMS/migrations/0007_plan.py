# Generated by Django 4.2.6 on 2023-11-04 16:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('TDMS', '0006_note'),
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_name', models.CharField(blank=True, max_length=255, null=True)),
                ('est_distance', models.FloatField(blank=True, null=True)),
                ('est_duration', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pendng', 'Pending'), ('accept', 'Accepted'), ('reject', 'Rejected'), ('cancel', 'Canceled'), ('progrs', 'In-progress'), ('complt', 'Complete')], default='pendng', max_length=6)),
                ('route_data', models.JSONField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
