from datetime import datetime

from django.db import models


# Create your models here.
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
