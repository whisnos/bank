# Generated by Django 2.1.5 on 2019-04-26 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spuser', '0002_auto_20190426_1429'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loginfo',
            name='log_type',
            field=models.IntegerField(choices=[(3, '用户记录'), (1, '订单记录'), (0, '登录记录'), (2, '提现记录')], verbose_name='操作类型'),
        ),
        migrations.AlterField(
            model_name='noticeinfo',
            name='notice_type',
            field=models.IntegerField(choices=[(1, '普通公告'), (2, '置顶')], default=0, verbose_name='公告类型'),
        ),
    ]