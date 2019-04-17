"""bank URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter
from .views import AdminProxyViewset, AdminuserProxyViewset, AdminChannelViewset, AdminOrderViewset, \
    AdminWithDrawViewset, AdminNoticeViewset, AdminCountViewset, AdminCUserViewset, AdminDeleteViewset, \
    AdminCDataViewset, GetPayView, AdminADataViewset, AdminWDataViewset, AdminCODataViewset, AdminChartViewset, \
    AdminCUDataViewset, AdminRateInfoViewset, AdminLogsViewset

route = DefaultRouter()
route.register(r'proxy', AdminProxyViewset, base_name="admin/proxy")
route.register(r'user', AdminuserProxyViewset, base_name="admin/user")
route.register(r'channel', AdminChannelViewset, base_name="admin/channel")
route.register(r'order', AdminOrderViewset, base_name="admin/order")
route.register(r'withdraw', AdminWithDrawViewset, base_name="admin/withdraw")
route.register(r'notice', AdminNoticeViewset, base_name="admin/notice")
route.register(r'count', AdminCountViewset, base_name="admin/count")
route.register(r'cuser', AdminCUserViewset, base_name="admin/cuser")
route.register(r'delete', AdminDeleteViewset, base_name="admin/delete")
route.register(r'cdata', AdminCDataViewset, base_name="admin/cdata")
route.register(r'wdata', AdminWDataViewset, base_name="admin/wdata")
route.register(r'adata', AdminADataViewset, base_name="admin/adata")
route.register(r'codata', AdminCODataViewset, base_name="admin/codata")
route.register(r'admin/cudata', AdminCUDataViewset, base_name="admin/cudata")
route.register(r'admin/chart', AdminChartViewset, base_name="admin/chart")
route.register(r'admin/rateinfo', AdminRateInfoViewset, base_name="admin/rateinfo")
route.register(r'admin/logs', AdminLogsViewset, base_name="admin/logs")
urlpatterns = [
    url(r'^', include(route.urls)),
    url(r'^test/$', GetPayView.as_view(), name="get_pay"),
]
