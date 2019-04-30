# Generated by Django 2.1.5 on 2019-04-30 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('channel', '0002_auto_20190426_1552'),
    ]

    operations = [
        migrations.AddField(
            model_name='alipayinfo',
            name='is_limit',
            field=models.BooleanField(default=False, verbose_name='是否限额'),
        ),
        migrations.AddField(
            model_name='alipayinfo',
            name='is_turn',
            field=models.BooleanField(default=False, verbose_name='轮流否'),
        ),
        migrations.AddField(
            model_name='alipayinfo',
            name='variable_money',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=9, verbose_name='满额'),
        ),
    ]
