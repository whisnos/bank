# Generated by Django 2.1.5 on 2019-05-03 15:31

import datetime
from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('web_url', models.CharField(blank=True, max_length=100, null=True, verbose_name='姓名')),
                ('level', models.IntegerField(choices=[(4, '财务'), (1, '管理员'), (2, '代理'), (3, '商户'), (5, '观察者')], default=3, verbose_name='用户等级')),
                ('money', models.DecimalField(decimal_places=2, default=0.0, max_digits=9, verbose_name='余额')),
                ('total_money', models.DecimalField(decimal_places=2, default=0.0, max_digits=9, verbose_name='总收款')),
                ('safe_code', models.CharField(default='e10adc3949ba59abbe56e057f20f883e', max_length=32, verbose_name='安全码')),
                ('uid', models.CharField(blank=True, max_length=50, null=True, verbose_name='用户uid')),
                ('auth_code', models.CharField(blank=True, max_length=32, null=True, verbose_name='用户授权码')),
                ('add_time', models.DateTimeField(default=datetime.datetime.now, verbose_name='注册时间')),
                ('mobile', models.CharField(blank=True, max_length=11, null=True, verbose_name='手机号')),
                ('is_google', models.BooleanField(default=False, verbose_name='是否谷歌')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('proxy', models.ForeignKey(blank=True, help_text='所属代理', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='proxys', to=settings.AUTH_USER_MODEL, verbose_name='所属代理')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': '用户管理',
                'verbose_name_plural': '用户管理',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Google2Auth',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=128, verbose_name='Google秘钥')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
