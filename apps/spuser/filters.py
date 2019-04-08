from django_filters import rest_framework as filters

from user.models import UserProfile


class AdminProxyFilter(filters.FilterSet):
    username = filters.CharFilter(field_name="username", lookup_expr='icontains', help_text="名称模糊查询")
    class Meta:
        model = UserProfile
        fields = ['username']


