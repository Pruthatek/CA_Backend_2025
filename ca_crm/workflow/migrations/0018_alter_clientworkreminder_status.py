# Generated by Django 4.2.17 on 2025-04-02 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0017_clientworkreminder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientworkreminder',
            name='status',
            field=models.CharField(blank=True, choices=[('close', 'Close'), ('open', 'Open')], default='open', max_length=15, null=True),
        ),
    ]
