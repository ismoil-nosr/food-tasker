# Generated by Django 3.0.8 on 2020-07-07 11:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodtaskerapp', '0004_localuser'),
    ]

    operations = [
        migrations.DeleteModel(
            name='LocalUser',
        ),
    ]
