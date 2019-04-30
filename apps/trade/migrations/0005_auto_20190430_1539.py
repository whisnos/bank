# Generated by Django 2.1.5 on 2019-04-30 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trade', '0004_auto_20190427_1449'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderinfo',
            name='pay_status',
            field=models.IntegerField(choices=[(3, '通知失败'), (0, '待支付'), (2, '支付关闭'), (1, '支付成功')], default=0, verbose_name='订单状态'),
        ),
    ]