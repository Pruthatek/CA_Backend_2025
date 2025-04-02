# Generated by Django 4.2.17 on 2025-04-01 12:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0008_inquiry_call_email_id_inquiry_call_full_name_and_more'),
        ('custom_auth', '0005_alter_customuser_address'),
        ('workflow', '0016_scheduletasktime_activities_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientWorkReminder',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('reminder_note', models.CharField(blank=True, max_length=400, null=True)),
                ('status', models.CharField(blank=True, max_length=100, null=True)),
                ('created_date', models.DateField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='client_work_reminder', to='clients.customer')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_by_work_reminder', to='custom_auth.customuser')),
                ('task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='task_work_reminder', to='workflow.clientworkcategoryassignment')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='updated_by_work_reminder', to='custom_auth.customuser')),
            ],
        ),
    ]
