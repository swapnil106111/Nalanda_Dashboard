# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2019-02-12 10:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sync_report', '0003_auto_20190212_0758'),
    ]

    operations = [
        migrations.AddField(
            model_name='last_sync_date',
            name='id_class_name',
            field=models.CharField(default=123, max_length=200),
            preserve_default=False,
        ),
    ]