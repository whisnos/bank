# Generated by Django 2.1.5 on 2019-05-03 15:39

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('nsm', '0001_initial'),
        ('proxy', '0002_auto_20190503_1531'),
        ('channel', '0002_alipayinfo_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pay_status', models.IntegerField(choices=[(3, '通知失败'), (0, '待支付'), (2, '支付关闭'), (1, '支付成功')], default=0, verbose_name='订单状态')),
                ('order_money', models.DecimalField(decimal_places=2, max_digits=7, verbose_name='订单金额')),
                ('real_money', models.DecimalField(decimal_places=2, max_digits=7, verbose_name='实际金额')),
                ('order_no', models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name='网站订单号')),
                ('order_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='商户订单号')),
                ('remark', models.CharField(blank=True, max_length=200, null=True, verbose_name='用户留言')),
                ('add_time', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
                ('pay_time', models.DateTimeField(blank=True, null=True, verbose_name='支付时间')),
                ('goods_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='货物名称')),
                ('proxy', models.IntegerField(blank=True, null=True, verbose_name='代理')),
                ('pay_url', models.TextField(blank=True, null=True, verbose_name='支付链接')),
                ('account_num', models.CharField(blank=True, max_length=32, null=True, verbose_name='银行卡号')),
                ('notify_url', models.CharField(blank=True, max_length=100, null=True, verbose_name='商户回调url')),
                ('service_money', models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True, verbose_name='费用')),
                ('trade_no', models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name='支付宝交易号')),
                ('out_trade_no', models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name='农商交易号')),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='channel.channelInfo', verbose_name='通道')),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='proxy.DeviceInfo', verbose_name='设备')),
                ('nsm', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nsm.NsshInfo', verbose_name='农商商户')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '订单管理',
                'verbose_name_plural': '订单管理',
            },
        ),
        migrations.CreateModel(
            name='WithDrawBankInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=20, verbose_name='收款人')),
                ('card_number', models.CharField(max_length=50, verbose_name='账号')),
                ('open_bank', models.CharField(blank=True, max_length=50, null=True, verbose_name='开户行')),
                ('bank_name', models.CharField(max_length=20, verbose_name='银行名称')),
                ('mobile', models.CharField(blank=True, max_length=11, null=True, verbose_name='手机号')),
                ('add_time', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '提现银行卡管理',
                'verbose_name_plural': '提现银行卡管理',
            },
        ),
        migrations.CreateModel(
            name='WithDrawInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('withdraw_no', models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='提现单号')),
                ('withdraw_status', models.IntegerField(choices=[(0, '处理中'), (1, '已处理'), (2, '驳回')], default=0, verbose_name='提现状态')),
                ('withdraw_money', models.DecimalField(decimal_places=2, max_digits=9, verbose_name='提现金额')),
                ('remark', models.CharField(blank=True, max_length=200, null=True, verbose_name='用户留言')),
                ('add_time', models.DateTimeField(default=datetime.datetime.now, verbose_name='提现时间')),
                ('receive_time', models.DateTimeField(blank=True, null=True, verbose_name='到账时间')),
                ('real_money', models.FloatField(blank=True, null=True, verbose_name='实际到账金额')),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trade.WithDrawBankInfo', verbose_name='收款信息')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '提现管理',
                'verbose_name_plural': '提现管理',
            },
        ),
    ]
