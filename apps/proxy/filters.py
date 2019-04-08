from django_filters import rest_framework as filters

from user.models import UserProfile


class ProxyUserFilter(filters.FilterSet):
    username = filters.CharFilter(field_name="username", lookup_expr='icontains', help_text="名称模糊查询")
    id = filters.NumberFilter(field_name='id',help_text="根据用户ID")
    class Meta:
        model = UserProfile
        fields = ['username','id']


# class DeviceFilter(filters.FilterSet):
#     username = filters.CharFilter(field_name="username", lookup_expr='icontains', help_text="名称模糊查询")
#
#     class Meta:
#         model = DeviceName
#         fields = ['username']
