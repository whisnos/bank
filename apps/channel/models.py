from django.db import models


# Create your models here.
class channelInfo(models.Model):
    # TYPE_CHOICE = {
    #     (0, 'atb'),
    #     (1, 'wang'),
    # }
    # channel_type = models.IntegerField(choices=TYPE_CHOICE, verbose_name='通道类型')
    channel_name = models.CharField(max_length=32, verbose_name='通道名称')

    class Meta:
        verbose_name = '通道管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.channel_name
