# Generated by Django 5.2 on 2025-05-02 19:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_rental_advance_paid_rental_is_advance_paid_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rental',
            name='remaining_amount',
        ),
    ]
