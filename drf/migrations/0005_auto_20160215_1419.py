# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('drf', '0004_auto_20160212_0110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='posttype',
            field=models.CharField(default=b'office', max_length=20),
        ),
    ]
