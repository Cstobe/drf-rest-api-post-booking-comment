# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.auth.models
import django.utils.timezone
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=30, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, verbose_name='username')),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('email', models.EmailField(max_length=254, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('birthday', models.DateField(null=True, blank=True)),
                ('phone_number', models.CharField(blank=True, max_length=17, validators=[django.core.validators.RegexValidator(regex=b'^\\+?1?\\d{9,15}$', message=b"Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")])),
                ('followers', models.ManyToManyField(related_name='followees', editable=False, to=settings.AUTH_USER_MODEL)),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                (b'objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField(null=True, blank=True)),
                ('status', models.CharField(default=b'approved', max_length=20)),
                ('created', models.DateTimeField(editable=False)),
                ('updated', models.DateTimeField()),
                ('author', models.ForeignKey(related_name='bookings', editable=False, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BookingDateTime',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('begin', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('status', models.CharField(default=b'approved', max_length=20)),
                ('author', models.ManyToManyField(related_name='bookingdatetime', editable=False, to=settings.AUTH_USER_MODEL)),
                ('booking', models.ManyToManyField(related_name='bookingdatetime', editable=False, to='drf.Booking')),
            ],
        ),
        migrations.CreateModel(
            name='BookingOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(default=b'per day limit to 100 person', max_length=20)),
                ('value', models.DecimalField(max_digits=5, decimal_places=2)),
                ('unit', models.CharField(default=b'RMB', max_length=10)),
                ('author', models.ForeignKey(related_name='options', editable=False, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(null=True, blank=True)),
                ('rating', models.PositiveIntegerField()),
                ('status', models.CharField(default=b'approved', max_length=20)),
                ('created', models.DateTimeField(editable=False)),
                ('updated', models.DateTimeField()),
                ('author', models.ForeignKey(related_name='comments', editable=False, to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(related_name='childs', blank=True, editable=False, to='drf.Comment')),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(default=b'post title', max_length=1000)),
                ('content', models.TextField(null=True, blank=True)),
                ('status', models.CharField(default=b'submitted', max_length=20)),
                ('type', models.CharField(default=b'office', max_length=20)),
                ('geoid', models.PositiveIntegerField()),
                ('created', models.DateTimeField(editable=False)),
                ('updated', models.DateTimeField()),
                ('author', models.ForeignKey(related_name='posts', editable=False, to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(related_name='childs', blank=True, editable=False, to='drf.Post')),
            ],
        ),
        migrations.CreateModel(
            name='PostImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'post image', max_length=100)),
                ('image', models.ImageField(max_length=1000, upload_to=b'postimage')),
                ('created', models.DateTimeField(editable=False)),
                ('updated', models.DateTimeField()),
                ('author', models.ForeignKey(related_name='images', editable=False, to=settings.AUTH_USER_MODEL)),
                ('post', models.ForeignKey(related_name='images', editable=False, to='drf.Post')),
            ],
        ),
        migrations.AddField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(related_name='comments', editable=False, to='drf.Post'),
        ),
        migrations.AddField(
            model_name='bookingoption',
            name='post',
            field=models.ForeignKey(related_name='options', editable=False, to='drf.Post'),
        ),
        migrations.AddField(
            model_name='bookingdatetime',
            name='post',
            field=models.ManyToManyField(related_name='bookingdatetime', editable=False, to='drf.Post'),
        ),
        migrations.AddField(
            model_name='booking',
            name='bookingoption',
            field=models.ForeignKey(related_name='bookings', editable=False, to='drf.BookingOption'),
        ),
        migrations.AddField(
            model_name='booking',
            name='post',
            field=models.ForeignKey(related_name='bookings', editable=False, to='drf.Post'),
        ),
    ]
