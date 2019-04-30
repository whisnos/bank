# Generated by Django 2.1.5 on 2019-04-26 14:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Google2Auth',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=128, verbose_name='Google秘钥')),
            ],
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_google',
            field=models.BooleanField(default=False, verbose_name='是否谷歌'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='level',
            field=models.IntegerField(choices=[(5, '观察者'), (1, '管理员'), (3, '商户'), (4, '财务'), (2, '代理')], default=3, verbose_name='用户等级'),
        ),
        migrations.AddField(
            model_name='google2auth',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
