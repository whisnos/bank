# Generated by Django 2.1.5 on 2019-04-26 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trade', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderinfo',
            name='pay_status',
            field=models.IntegerField(choices=[(1, '支付成功'), (0, '待支付'), (2, '支付关闭'), (3, '通知失败')], default=0, verbose_name='订单状态'),
        ),
    ]
