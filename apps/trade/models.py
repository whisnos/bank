from datetime import datetime

from django.db import models

# Create your models here.
from channel.models import channelInfo
from proxy.models import DeviceInfo
from user.models import UserProfile
from nsm.models import NsshInfo

class OrderInfo(models.Model):
    PAY_STATUS = {
        (0, '待支付'),
        (1, '支付成功'),
        (2, '支付关闭'),
        (3, '通知失败'),
    }
    pay_status = models.IntegerField(default=0, choices=PAY_STATUS, verbose_name='订单状态')
    order_money = models.DecimalField(verbose_name='订单金额', max_digits=7, decimal_places=2)
    real_money = models.DecimalField(verbose_name='实际金额', max_digits=7, decimal_places=2)
    order_no = models.CharField(max_length=100, unique=True, null=True, blank=True,verbose_name='网站订单号')
    order_id = models.CharField(max_length=100, null=True, blank=True, verbose_name='商户订单号')
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name='用户留言')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='创建时间')
    pay_time = models.DateTimeField(null=True, blank=True, verbose_name="支付时间")
    # order_channel 订单通道
    # order_uid
    goods_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='货物名称')
    channel = models.ForeignKey(channelInfo, verbose_name='通道', on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, verbose_name='用户', on_delete=models.CASCADE)
    proxy = models.IntegerField(null=True, blank=True, verbose_name='代理')
    pay_url = models.TextField(null=True, blank=True, verbose_name='支付链接')
    device = models.ForeignKey(DeviceInfo,on_delete=models.CASCADE, null=True, blank=True,verbose_name='设备')
    account_num = models.CharField(max_length=32, null=True, blank=True, verbose_name='银行卡号')
    notify_url = models.CharField(max_length=100, null=True, blank=True, verbose_name='商户回调url')
    service_money = models.DecimalField(verbose_name='费用', max_digits=7, decimal_places=2, null=True, blank=True)
    trade_no = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='支付宝交易号')
    out_trade_no = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='农商交易号')
    nsm = models.ForeignKey(NsshInfo, on_delete=models.CASCADE, null=True, blank=True, verbose_name='农商商户')
    def __str__(self):
        return str(self.order_no)

    class Meta:
        verbose_name = '订单管理'
        verbose_name_plural = verbose_name


class WithDrawBankInfo(models.Model):
    username = models.CharField(max_length=20, verbose_name='收款人')
    card_number = models.CharField(max_length=50, verbose_name='账号')
    open_bank = models.CharField(max_length=50, null=True, blank=True, verbose_name='开户行')
    bank_name = models.CharField(max_length=20, verbose_name='银行名称')
    mobile = models.CharField(max_length=11, null=True, blank=True,verbose_name='手机号')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='创建时间')
    user = models.ForeignKey(UserProfile, verbose_name='用户', on_delete=models.CASCADE)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = '提现银行卡管理'
        verbose_name_plural = verbose_name


class WithDrawInfo(models.Model):
    withdraw_no = models.CharField(max_length=50, unique=True, verbose_name='提现单号', null=True, blank=True)
    withdraw_status = models.IntegerField(
        choices=((0, '处理中'), (1, '已处理'), (2, '驳回')),
        default=0, verbose_name='提现状态')
    withdraw_money = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='提现金额')
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name='用户留言')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='提现时间')
    receive_time = models.DateTimeField(null=True, blank=True, verbose_name='到账时间')
    user = models.ForeignKey(UserProfile, verbose_name='用户', on_delete=models.CASCADE)
    real_money = models.FloatField(null=True, blank=True, verbose_name='实际到账金额')
    bank = models.ForeignKey(WithDrawBankInfo, verbose_name='收款信息', on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = '提现管理'
        verbose_name_plural = verbose_name
