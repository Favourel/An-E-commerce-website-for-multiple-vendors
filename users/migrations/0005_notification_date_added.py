# Generated by Django 3.0.8 on 2021-01-16 23:40

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='date_added',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
