from django_filters import rest_framework as filters

from proxy.models import DeviceInfo, ReceiveBankInfo
from trade.models import OrderInfo, WithDrawInfo, WithDrawBankInfo
from user.models import UserProfile


class ProxyUserFilter(filters.FilterSet):
    username = filters.CharFilter(field_name="username", lookup_expr='icontains', help_text="名称模糊查询")
    id = filters.NumberFilter(field_name='id', help_text="根据用户ID")

    class Meta:
        model = UserProfile
        fields = ['username', 'id']


class OrdersFilter(filters.FilterSet):
    # min_price = filters.NumberFilter(field_name='real_money', lookup_expr='gte')
    # max_price = filters.NumberFilter(field_name="real_money", lookup_expr='lte', help_text="最大金额")
    pay_status = filters.CharFilter(field_name='pay_status', lookup_expr='icontains')
    order_no = filters.CharFilter(field_name="order_no", lookup_expr='icontains', help_text="订单名称模糊查询")
    # order_id = filters.CharFilter(field_name="order_id", help_text="商家订单名称模糊查询")
    # remark = filters.CharFilter(field_name="remark", lookup_expr='icontains')
    start_time = filters.DateTimeFilter(field_name='add_time', lookup_expr='gte')
    end_time = filters.DateTimeFilter(field_name='add_time', lookup_expr='lte')
    userid = filters.NumberFilter(field_name='user_id', help_text="根据用户ID")
    deviceid =filters.NumberFilter(field_name='device_id', help_text="根据用户ID")
    class Meta:
        model = OrderInfo
        fields = ['order_no', 'order_id', 'start_time', 'end_time', 'userid','deviceid']


# class DeviceFilter(filters.FilterSet):
#     username = filters.CharFilter(field_name="username", lookup_expr='icontains', help_text="名称模糊查询")
#
#     class Meta:
#         model = DeviceName
#         fields = ['username']

class WithDrawFilter(filters.FilterSet):
    card_number = filters.CharFilter(field_name='withdraw_status', lookup_expr='icontains')
    withdraw_no = filters.CharFilter(field_name="withdraw_no", lookup_expr='icontains', help_text="订单名称模糊查询")
    start_time = filters.DateTimeFilter(field_name='add_time', lookup_expr='gte')
    end_time = filters.DateTimeFilter(field_name='add_time', lookup_expr='lte')

    class Meta:
        model = WithDrawInfo
        fields = ['withdraw_no', 'withdraw_status', 'start_time', 'end_time']


class DeviceFilter(filters.FilterSet):
    device_name = filters.CharFilter(field_name='device_name', lookup_expr='icontains')

    class Meta:
        model = DeviceInfo
        fields = ['device_name']


class ReceiveBankFilter(filters.FilterSet):
    card_number = filters.CharFilter(field_name='card_number', lookup_expr='icontains')
    bank_type = filters.CharFilter(field_name='bank_type', lookup_expr='icontains')

    class Meta:
        model = ReceiveBankInfo
        fields = ['card_number', 'bank_type']

class WithDrawBankFilter(filters.FilterSet):
    card_number = filters.CharFilter(field_name='card_number', lookup_expr='icontains')

    class Meta:
        model = WithDrawBankInfo
        fields = ['card_number']