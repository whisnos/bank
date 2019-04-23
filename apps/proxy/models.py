from datetime import datetime

from django.db import models

# Create your models here.
# 费率表(rateinfo)
# 费率 (decimal----rate)
# 映射状态(bool----is_map)
# 映射名称(int----mapid)
# 用户外键(foreignkey----user)
# 通道外键(foreignkey----channel)
from channel.models import channelInfo
from user.models import UserProfile


class RateInfo(models.Model):
    rate = models.DecimalField(max_digits=4, decimal_places=3,default=0.015, verbose_name='费率')
    user = models.ForeignKey(UserProfile, verbose_name='用户', on_delete=models.CASCADE)
    channel = models.ForeignKey(channelInfo, verbose_name='通道', on_delete=models.CASCADE)
    is_map = models.BooleanField(default=False, verbose_name='是否映射')
    mapid = models.IntegerField(null=True, blank=True, verbose_name='映射id')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='创建时间')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = '费率管理'
        verbose_name_plural = verbose_name
        unique_together=['user','channel']

class DeviceInfo(models.Model):
    device_name = models.CharField(max_length=25, unique=True, verbose_name='设备名称')
    password = models.CharField(max_length=15, verbose_name='密码')
    total_money = models.DecimalField(max_digits=9, decimal_places=2, default=0.00, verbose_name='总收款')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='创建时间')
    is_active = models.BooleanField(default=False, verbose_name='是否激活')
    user = models.ForeignKey(UserProfile, verbose_name='用户', on_delete=models.CASCADE)
    auth_code = models.CharField(max_length=32, null=True, blank=True, verbose_name='用户验证码')
    class Meta:
        verbose_name = '设备管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.device_name



class ReceiveBankInfo(models.Model):
    # 收款人(string----username)
    username = models.CharField(max_length=50, verbose_name='收款人')
    # 账号(string----card_number)
    card_number = models.CharField(max_length=35, unique=True, verbose_name='账号')
    # 银行类型(int----bank_type)
    bank_type = models.CharField(max_length=15, verbose_name='银行类型')
    # 手机号码(string----mobile)
    mobile = models.CharField(max_length=11, null=True, blank=True, verbose_name='手机号')
    # 创建时间(datetime----add_time)
    add_time = models.DateTimeField(default=datetime.now, verbose_name='创建时间')
    # 卡索引(string----card_index)
    card_index = models.CharField(max_length=32, verbose_name='卡索引')
    # 银行电话(string----bank_tel)
    bank_tel = models.CharField(max_length=15, null=True, blank=True, verbose_name='银行电话')
    # 银行编号(string----bank_mark)
    bank_mark = models.CharField(max_length=20, null=True, blank=True, verbose_name='银行编号')
    # 激活状态(int----is_active)
    is_active = models.BooleanField(default=False, verbose_name='是否激活')
    # 总收款(decimal----total_money)
    total_money = models.DecimalField(max_digits=9, decimal_places=2, default=0.00, verbose_name='总收款')
    # 设备外键(foreignkey----device)
    # device = models.ForeignKey(DeviceInfo, verbose_name='对应设备',
    #                            on_delete=models.CASCADE)
    device = models.IntegerField(verbose_name='对应设备',null=True, blank=True)
    # 用户外键(foreignkey----user)
    user = models.ForeignKey(UserProfile, verbose_name='对应用户',
                             on_delete=models.CASCADE)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = '收款管理'
        verbose_name_plural = verbose_name

class DeviceChannelInfo(models.Model):
    device = models.ForeignKey(DeviceInfo,on_delete=models.CASCADE)
    channel = models.ForeignKey(channelInfo,on_delete=models.CASCADE)
    add_time = models.DateTimeField(default=datetime.now, verbose_name='创建时间')
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.id

    class Meta:
        verbose_name = '设备通道表'
        verbose_name_plural = verbose_name