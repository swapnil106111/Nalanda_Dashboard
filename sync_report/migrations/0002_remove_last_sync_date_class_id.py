# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2019-02-12 07:53
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sync_report', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='last_sync_date',
            name='class_id',
        ),
    ]