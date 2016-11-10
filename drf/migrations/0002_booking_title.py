# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('drf', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='title',
            field=models.CharField(default=b'booking title', max_length=1000),
        ),
    ]
