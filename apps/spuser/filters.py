from django_filters import rest_framework as filters

from channel.models import channelInfo
from spuser.models import LogInfo
from trade.models import OrderInfo, WithDrawInfo
from user.models import UserProfile


class AdminProxyFilter(filters.FilterSet):
    username = filters.CharFilter(field_name="username", lookup_expr='icontains', help_text="名称模糊查询")

    class Meta:
        model = UserProfile
        fields = ['username']


class AdminChannelFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="channel_name", lookup_expr='icontains', help_text="名称模糊查询")

    class Meta:
        model = channelInfo
        fields = ['name']


class AdminOrderFilter(filters.FilterSet):
    pay_status = filters.NumberFilter(field_name='pay_status')
    order_no = filters.CharFilter(field_name="order_no", lookup_expr='icontains', help_text="订单名称模糊查询")
    start_time = filters.DateTimeFilter(field_name='add_time', lookup_expr='gte')
    end_time = filters.DateTimeFilter(field_name='add_time', lookup_expr='lte')
    userid = filters.NumberFilter(field_name='user_id', help_text="根据用户ID")
    proxyid = filters.NumberFilter(field_name='proxy', help_text="根据代理ID")
    channelid = filters.NumberFilter(field_name='channel_id', help_text="根据设备ID")
    order_id = filters.CharFilter(field_name="order_id", lookup_expr='icontains', help_text="订单名称模糊查询")
    min_price = filters.NumberFilter(field_name='real_money', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="real_money", lookup_expr='lte', help_text="最大金额")

    class Meta:
        model = OrderInfo
        fields = ['order_no', 'order_id', 'start_time', 'end_time', 'userid', 'proxyid', 'channelid', 'order_id',
                  'min_price', 'max_price']
class LogFilter(filters.FilterSet):
    content = filters.CharFilter(field_name="content", lookup_expr='icontains', help_text="名称查询")
    start_time = filters.DateTimeFilter(field_name='add_time', lookup_expr='gte')
    end_time = filters.DateTimeFilter(field_name='add_time', lookup_expr='lte')
    userid = filters.NumberFilter(field_name='user_id', help_text="根据用户ID")
    log_type = filters.NumberFilter(field_name='log_type',help_text="根据类型过滤")
    class Meta:
        model = LogInfo
        fields = ['content','start_time','end_time','userid','log_type']