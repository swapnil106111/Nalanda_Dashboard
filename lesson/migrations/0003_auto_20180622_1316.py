# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-22 13:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lesson', '0002_auto_20180621_0604'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='lesson_id',
            field=models.CharField(max_length=60, primary_key=True, serialize=False),
        ),
    ]
