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
from rest_framework_jwt.views import obtain_jwt_token

route = DefaultRouter()
from user.views import UserInfoViewset, UserOrderViewset, UserWithDrawViewset, UserWithDrawBankViewset, \
    UserCountViewset, UserCDataViewset, UserADataViewset, UserWDataViewset, GetPayView, UserCODataViewset,UserChartViewset

# user
route.register(r'user/info', UserInfoViewset, base_name="user/info")
route.register(r'user/order', UserOrderViewset, base_name="user/order")
route.register(r'user/withdraw', UserWithDrawViewset, base_name="user/withdraw")
route.register(r'user/withdrawbank', UserWithDrawBankViewset, base_name="user/withdrawbank")
route.register(r'user/count', UserCountViewset, base_name="user/count")
route.register(r'user/cdata', UserCDataViewset, base_name="user/cdata")
route.register(r'user/wdata', UserWDataViewset, base_name="user/wdata")
route.register(r'user/adata', UserADataViewset, base_name="user/adata")
route.register(r'user/codata', UserCODataViewset, base_name="user/codata")
route.register(r'user/chart', UserChartViewset, base_name="user/chart")

# proxy
from proxy.views import ProxyUserInfoViewset, ProxyRateInfoViewset, ProxyOrderInfoViewset, ProxyWithDrawViewset, \
    ProxyDeviceViewset, ProxyReceiveBankViewset, ProxyCountViewset, ProxyCDatatViewset, ProxyADataViewset, \
    ProxyWDatatViewset, ProxyCODataViewset,ProxyChartViewset,ProxyCUDataViewset

route.register(r'proxy/user', ProxyUserInfoViewset, base_name="proxy/info")
route.register(r'proxy/rateinfo', ProxyRateInfoViewset, base_name="proxy/rateinfo")
route.register(r'proxy/order', ProxyOrderInfoViewset, base_name="proxy/order")
route.register(r'proxy/withdraw', ProxyWithDrawViewset, base_name="proxy/withdraw")
route.register(r'proxy/device', ProxyDeviceViewset, base_name="proxy/device")
route.register(r'proxy/receivebankinfo', ProxyReceiveBankViewset, base_name="proxy/receivebankinfo")
route.register(r'proxy/count', ProxyCountViewset, base_name="proxy/count")
route.register(r'proxy/cdata', ProxyCDatatViewset, base_name="proxy/cdata")
route.register(r'proxy/wdata', ProxyWDatatViewset, base_name="proxy/wdata")
route.register(r'proxy/adata', ProxyADataViewset, base_name="proxy/adata")
route.register(r'proxy/codata', ProxyCODataViewset, base_name="proxy/codata")
route.register(r'proxy/cudata', ProxyCUDataViewset, base_name="proxy/cudata")
route.register(r'proxy/chart', ProxyChartViewset, base_name="proxy/chart")
# admin
from spuser.views import AdminProxyViewset, AdminuserProxyViewset, AdminChannelViewset, AdminOrderViewset, \
    AdminWithDrawViewset, AdminNoticeViewset, AdminCountViewset, PublicChannelViewset, PublicNoticeViewset, \
    AdminCUserViewset, AdminDeleteViewset, AdminCDataViewset, AdminADataViewset, AdminWDataViewset, AdminCODataViewset, \
    AdminChartViewset,AdminCUDataViewset

route.register(r'admin/proxy', AdminProxyViewset, base_name="admin/proxy")
route.register(r'admin/user', AdminuserProxyViewset, base_name="admin/user")
route.register(r'admin/channel', AdminChannelViewset, base_name="admin/channel")
route.register(r'admin/order', AdminOrderViewset, base_name="admin/order")
route.register(r'admin/withdraw', AdminWithDrawViewset, base_name="admin/withdraw")
route.register(r'admin/notice', AdminNoticeViewset, base_name="admin/notice")
route.register(r'admin/count', AdminCountViewset, base_name="admin/count")
route.register(r'admin/cuser', AdminCUserViewset, base_name="admin/cuser")
route.register(r'admin/delete', AdminDeleteViewset, base_name="admin/delete")
route.register(r'admin/cdata', AdminCDataViewset, base_name="admin/cdata")
route.register(r'admin/wdata', AdminWDataViewset, base_name="admin/wdata")
route.register(r'admin/adata', AdminADataViewset, base_name="admin/adata")
route.register(r'admin/codata', AdminCODataViewset, base_name="admin/codata")
route.register(r'admin/cudata', AdminCUDataViewset, base_name="admin/cudata")
route.register(r'admin/chart', AdminChartViewset, base_name="admin/chart")

# public

route.register(r'public/channel', PublicChannelViewset, base_name="public/channel")
route.register(r'public/notice', PublicNoticeViewset, base_name="public/notice")

# directly

urlpatterns = [
    url(r'^', include(route.urls)),
    url(r'^user/', include('user.urls')),
    url(r'^proxy/', include('proxy.urls')),
    url(r'^admin/', include('spuser.urls')),
    url(r'^public/', include('spuser.url')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^login/$', obtain_jwt_token),
    url(r'^get_pay/$', GetPayView.as_view(), name="get_pay"),
]
