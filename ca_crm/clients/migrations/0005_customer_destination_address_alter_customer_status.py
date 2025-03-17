# Generated by Django 4.2.17 on 2025-03-17 05:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_customerbranch_remove_customer_first_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='destination_address',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='status',
            field=models.CharField(blank=True, choices=[('proprietor', 'Proprietor'), ('firm', 'Firm'), ('private_limited', 'Private Limited'), ('public_limited', 'Public Limited'), ('bank', 'Bank'), ('aop_or_boi', 'AOP Or BOI'), ('huf', 'HUF'), ('ajp', 'AJP'), ('society', 'Society'), ('individual', 'Individual')], max_length=50, null=True),
        ),
    ]
