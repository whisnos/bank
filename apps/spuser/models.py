from datetime import datetime

from django.db import models


# Create your models here.
from user.models import UserProfile


class NoticeInfo(models.Model):
    NOTICE_STATUS = {
        (1, '普通公告'),
        (2, '置顶')
    }
    title = models.CharField(max_length=100, verbose_name='公告标题')
    content = models.TextField(verbose_name='公告内容')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='创建时间')
    notice_type = models.IntegerField(choices=NOTICE_STATUS, default=0, verbose_name='公告类型')

    class Meta:
        verbose_name = '公告管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title

class LogInfo(models.Model):
    OPERATE_STATUS = {
        (0, '登录记录'),  # 登录ip
        (1, '订单记录'),  # 创建 状态记录
        (2, '提现记录'),  # 创建 审核 驳回
        (3, '用户记录'),  # 创建 修改密码 费率 加款 扣款
    }
    log_type = models.IntegerField(choices=OPERATE_STATUS, verbose_name='操作类型')
    content = models.CharField(max_length=400, verbose_name='日志内容')
    user = models.ForeignKey(UserProfile, related_name='logs', verbose_name='用户',
                             on_delete=models.CASCADE)
    add_time = models.DateTimeField(default=datetime.now, verbose_name='创建时间')

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = '操作日志'
        verbose_name_plural = verbose_name