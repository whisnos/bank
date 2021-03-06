# Generated by Django 2.1.5 on 2019-05-03 15:31

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceChannelInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('add_time', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': '设备通道表',
                'verbose_name_plural': '设备通道表',
            },
        ),
        migrations.CreateModel(
            name='DeviceInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_name', models.CharField(max_length=25, unique=True, verbose_name='设备名称')),
                ('password', models.CharField(max_length=15, verbose_name='密码')),
                ('total_money', models.DecimalField(decimal_places=2, default=0.0, max_digits=9, verbose_name='总收款')),
                ('add_time', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
                ('is_active', models.BooleanField(default=False, verbose_name='是否激活')),
                ('auth_code', models.CharField(blank=True, max_length=32, null=True, verbose_name='用户验证码')),
            ],
            options={
                'verbose_name': '设备管理',
                'verbose_name_plural': '设备管理',
            },
        ),
        migrations.CreateModel(
            name='RateInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.DecimalField(decimal_places=3, default=0.015, max_digits=4, verbose_name='费率')),
                ('is_map', models.BooleanField(default=False, verbose_name='是否映射')),
                ('mapid', models.IntegerField(blank=True, null=True, verbose_name='映射id')),
                ('add_time', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否激活')),
            ],
            options={
                'verbose_name': '费率管理',
                'verbose_name_plural': '费率管理',
            },
        ),
        migrations.CreateModel(
            name='ReceiveBankInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=50, verbose_name='收款人')),
                ('card_number', models.CharField(max_length=35, unique=True, verbose_name='账号')),
                ('bank_type', models.CharField(max_length=15, verbose_name='银行类型')),
                ('mobile', models.CharField(blank=True, max_length=11, null=True, verbose_name='手机号')),
                ('add_time', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
                ('card_index', models.CharField(max_length=32, verbose_name='卡索引')),
                ('bank_tel', models.CharField(blank=True, max_length=15, null=True, verbose_name='银行电话')),
                ('bank_mark', models.CharField(blank=True, max_length=20, null=True, verbose_name='银行编号')),
                ('is_active', models.BooleanField(default=False, verbose_name='是否激活')),
                ('total_money', models.DecimalField(decimal_places=2, default=0.0, max_digits=9, verbose_name='总收款')),
                ('device', models.IntegerField(blank=True, null=True, verbose_name='对应设备')),
            ],
            options={
                'verbose_name': '收款管理',
                'verbose_name_plural': '收款管理',
            },
        ),
    ]
