# Generated by Django 3.1.7 on 2021-08-19 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Trequest', '0058_auto_20210817_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='driverevaluation',
            name='rating',
            field=models.CharField(max_length=1),
        ),
    ]
