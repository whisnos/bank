from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime
# Create your models here.
class UserProfile(AbstractUser):
    web_url = models.CharField(max_length=100, null=True, blank=True, verbose_name='姓名')
    level = models.IntegerField(default=3, verbose_name='用户等级')  # 1 超级用户 2 tuoxie 3 tuoxie001
    money = models.DecimalField(max_digits=9,decimal_places=2,default=0.00,verbose_name='余额')
    total_money = models.DecimalField(max_digits=9,decimal_places=2,default=0.00,verbose_name='总收款')
    safe_code = models.CharField(max_length=32, default='e10adc3949ba59abbe56e057f20f883e', verbose_name='安全码')
    uid = models.CharField(max_length=50, null=True, blank=True, verbose_name='用户uid')
    auth_code = models.CharField(max_length=32, null=True, blank=True, verbose_name='用户授权码')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='注册时间')
    mobile = models.CharField(max_length=11, null=True, blank=True, verbose_name='手机号')
    proxy = models.ForeignKey("self", null=True, blank=True, verbose_name="所属代理", help_text="所属代理",
                              related_name="proxys", on_delete=models.CASCADE)
    # is_proxy = models.BooleanField(default=False, verbose_name='是否代理')

    class Meta:
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username