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
from django.conf.urls import url,include

from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token

route = DefaultRouter()
from user.views import UserInfoViewset, UserOrderViewset, UserWithDrawViewset, UserWithDrawBankViewset, UserCountViewset

# user
route.register(r'user/info', UserInfoViewset, base_name="user/info")
route.register(r'user/order', UserOrderViewset, base_name="user/order")
route.register(r'user/withdraw', UserWithDrawViewset, base_name="user/withdraw")
route.register(r'user/withdrawbank', UserWithDrawBankViewset, base_name="user/withdrawbank")
route.register(r'user/count', UserCountViewset, base_name="user/count")
# proxy
from proxy.views import ProxyUserInfoViewset, ProxyRateInfoViewset, ProxyOrderInfoViewset, ProxyWithDrawViewset, \
    ProxyDeviceViewset, ProxyReceiveBankViewset, ProxyCountViewset

route.register(r'proxy/user', ProxyUserInfoViewset, base_name="proxy/info")
route.register(r'proxy/rateinfo', ProxyRateInfoViewset, base_name="proxy/rateinfo")
route.register(r'proxy/order', ProxyOrderInfoViewset, base_name="proxy/order")
route.register(r'proxy/withdraw', ProxyWithDrawViewset, base_name="proxy/withdraw")
route.register(r'proxy/device', ProxyDeviceViewset, base_name="proxy/device")
route.register(r'proxy/receivebankinfo', ProxyReceiveBankViewset, base_name="proxy/receivebankinfo")
route.register(r'proxy/count', ProxyCountViewset, base_name="proxy/count")
# admin
from spuser.views import AdminProxyViewset, AdminuserProxyViewset, AdminChannelViewset, AdminOrderViewset, \
    AdminWithDrawViewset, AdminNoticeViewset, AdminCountViewset

route.register(r'admin/proxy', AdminProxyViewset, base_name="admin/proxy")
route.register(r'admin/user', AdminuserProxyViewset, base_name="admin/user")
route.register(r'admin/channel', AdminChannelViewset, base_name="admin/channel")
route.register(r'admin/order', AdminOrderViewset, base_name="admin/order")
route.register(r'admin/withdraw', AdminWithDrawViewset, base_name="admin/withdraw")
route.register(r'admin/notice', AdminNoticeViewset, base_name="admin/notice")
route.register(r'admin/count', AdminCountViewset, base_name="admin/count")
# public
from spuser.views import AdminChannelViewset, AdminNoticeViewset

route.register(r'public/channel', AdminChannelViewset, base_name="public/channel")
route.register(r'public/notice', AdminNoticeViewset, base_name="public/notice")

urlpatterns = [
    url(r'^', include(route.urls)),
    url(r'^user/', include('user.urls')),
    url(r'^proxy/', include('proxy.urls')),
    url(r'^admin/', include('spuser.urls')),
    url(r'^public/', include('spuser.url')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^login/$', obtain_jwt_token),
]
