# Generated by Django 3.0.8 on 2021-01-08 00:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_category_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='count',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
