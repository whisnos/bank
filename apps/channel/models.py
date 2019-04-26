from datetime import datetime

from django.db import models

# Create your models here.
from user.models import UserProfile


class channelInfo(models.Model):
    # TYPE_CHOICE = {
    #     (0, 'atb'),
    #     (1, 'wang'),
    # }
    # channel_type = models.IntegerField(choices=TYPE_CHOICE, verbose_name='通道类型')
    channel_name = models.CharField(max_length=32, verbose_name='通道名称')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='创建时间')

    class Meta:
        verbose_name = '通道管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.channel_name


class AlipayInfo(models.Model):
    name = models.CharField(max_length=50, verbose_name='收款公司名称')
    c_appid = models.CharField(max_length=32, verbose_name='商家支付宝appid',unique=True)
    alipay_public_key = models.TextField(verbose_name='支付宝公钥')
    c_private_key = models.TextField(verbose_name='商家私钥')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='创建时间')
    is_active = models.BooleanField(default=True, verbose_name='是否激活状态')
    last_time = models.DateTimeField(null=True, blank=True, verbose_name='最后收款时间')
    total_money = models.DecimalField(max_digits=9, decimal_places=2, default=0.0, verbose_name='总收款')
    user = models.ForeignKey(UserProfile, verbose_name='所属代理', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '支付宝管理'
        verbose_name_plural = verbose_name
