# Generated by Django 3.2.4 on 2021-08-01 22:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Trequest', '0039_profile_bio'),
    ]

    operations = [
        migrations.CreateModel(
            name='MaterialRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('new_material_model', models.CharField(max_length=200)),
                ('quantity_of_new', models.PositiveIntegerField()),
                ('quantity_of_old', models.PositiveIntegerField()),
                ('old_material_model', models.CharField(max_length=200)),
                ('status', models.CharField(choices=[('Reusable', 'reusable'), ('Usable', 'usable')], max_length=200, null=True)),
                ('new_material_name', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='new_material', to='Trequest.material')),
                ('old_material_name', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='old_material', to='Trequest.material')),
                ('vehicle_model', models.ForeignKey(max_length=200, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='Trequest.vehicle')),
            ],
        ),
    ]
