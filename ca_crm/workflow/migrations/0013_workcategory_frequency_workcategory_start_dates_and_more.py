# Generated by Django 4.2.17 on 2025-03-20 11:34

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0012_assignedworkactivity_display_order_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workcategory',
            name='frequency',
            field=models.CharField(blank=True, choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly'), ('quarterly', 'Quarterly'), ('half_yearly', 'Half Yearly'), ('other', 'Other')], max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='workcategory',
            name='start_dates',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='WorkCategoryDate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_type', models.CharField(choices=[('monthly', 'Monthly (e.g., 13th of every month)'), ('yearly', 'Yearly (e.g., 15th March)')], default='monthly', max_length=10)),
                ('day', models.PositiveIntegerField(help_text='Day of the month (1-31). Required for all types.', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(31)])),
                ('month', models.PositiveIntegerField(blank=True, help_text="Month (1-12). Required for 'yearly' type.", null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
                ('work_category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dates', to='workflow.workcategory')),
            ],
        ),
    ]
