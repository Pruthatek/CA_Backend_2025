# Generated by Django 4.2.17 on 2025-04-03 09:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('custom_auth', '0005_alter_customuser_address'),
        ('billing', '0007_billing_cgst_billing_cgst_amount_billing_sgst_and_more'),
        ('clients', '0010_alter_inquiry_call_relation_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reminders',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('type_of_reminder', models.CharField(blank=True, max_length=100, null=True)),
                ('reminder_title', models.CharField(blank=True, max_length=200, null=True)),
                ('content', models.TextField(blank=True, null=True)),
                ('reminder_date', models.DateField(blank=True, null=True)),
                ('to_email', models.CharField(blank=True, max_length=200, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('billing', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='billing_reminder', to='billing.billing')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminder_created_by', to='custom_auth.customuser')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_reminder', to='clients.customer')),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reminder_updated_by', to='custom_auth.customuser')),
            ],
        ),
    ]
