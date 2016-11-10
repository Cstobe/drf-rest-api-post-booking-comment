# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('drf', '0003_auto_20160209_1417'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='posttype',
            field=models.CharField(default=b'office', max_length=40),
        ),
    ]
