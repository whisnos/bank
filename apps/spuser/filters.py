from django_filters import rest_framework as filters

from trade.models import OrderInfo, WithDrawInfo
from user.models import UserProfile


class AdminProxyFilter(filters.FilterSet):
    username = filters.CharFilter(field_name="username", lookup_expr='icontains', help_text="名称模糊查询")
    class Meta:
        model = UserProfile
        fields = ['username']


class AdminOrderFilter(filters.FilterSet):
    pay_status = filters.CharFilter(field_name='pay_status', lookup_expr='icontains')
    order_no = filters.CharFilter(field_name="order_no", lookup_expr='icontains', help_text="订单名称模糊查询")
    start_time = filters.DateTimeFilter(field_name='add_time', lookup_expr='gte')
    end_time = filters.DateTimeFilter(field_name='add_time', lookup_expr='lte')
    userid = filters.NumberFilter(field_name='user_id', help_text="根据用户ID")

    class Meta:
        model = OrderInfo
        fields = ['order_no', 'order_id', 'start_time', 'end_time', 'userid']