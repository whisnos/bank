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
    rate = models.DecimalField(max_digits=4, decimal_places=3, verbose_name='费率')
    user = models.ForeignKey(UserProfile, verbose_name='用户', on_delete=models.CASCADE)
    channel = models.ForeignKey(channelInfo, verbose_name='通道', on_delete=models.CASCADE)
    is_map = models.BooleanField(default=False, verbose_name='是否映射')
    mapid = models.IntegerField(null=True, blank=True, verbose_name='映射id')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='创建时间')
    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = '费率管理'
        verbose_name_plural = verbose_name