# Generated by Django 2.1.5 on 2019-05-03 15:31

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LogInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('log_type', models.IntegerField(choices=[(3, '用户记录'), (0, '登录记录'), (2, '提现记录'), (1, '订单记录')], verbose_name='操作类型')),
                ('content', models.CharField(max_length=400, verbose_name='日志内容')),
                ('add_time', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
            ],
            options={
                'verbose_name': '操作日志',
                'verbose_name_plural': '操作日志',
            },
        ),
        migrations.CreateModel(
            name='NoticeInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='公告标题')),
                ('content', models.TextField(verbose_name='公告内容')),
                ('add_time', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
                ('notice_type', models.IntegerField(choices=[(1, '普通公告'), (2, '置顶')], default=0, verbose_name='公告类型')),
            ],
            options={
                'verbose_name': '公告管理',
                'verbose_name_plural': '公告管理',
            },
        ),
    ]
