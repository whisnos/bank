from django.db import models
from datetime import datetime

from user.models import UserProfile


class NsshInfo(models.Model):
    appid = models.CharField(max_length=100, null=True, blank=True, verbose_name='农商appid')
    mch_name = models.CharField(max_length=100, null=True, blank=True)
    money = models.DecimalField(default=0, max_digits=11, decimal_places=2)
    add_time = models.DateTimeField(default=datetime.now)
    user = models.ForeignKey(UserProfile, verbose_name='所属代理', on_delete=models.CASCADE, null=True, blank=True, )
    is_limit = models.BooleanField(default=False, verbose_name='是否限额')
    variable_money = models.DecimalField(max_digits=9, decimal_places=2, default=0.0, verbose_name='满额')
    is_turn = models.BooleanField(default=False, verbose_name='轮流否')  # 0 未收过 1 已收过
    is_active = models.BooleanField(default=True, verbose_name='是否激活')

    def __str__(self):
        return self.appid
