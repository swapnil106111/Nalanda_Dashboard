# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-29 14:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LatestFetchDate',
            fields=[
                ('date_id', models.IntegerField(primary_key=True, serialize=False)),
                ('latest_date', models.DateTimeField()),
            ],
        ),
    ]