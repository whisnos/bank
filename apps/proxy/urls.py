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
from .views import ProxyUserInfoViewset, ProxyRateInfoViewset, ProxyOrderInfoViewset, ProxyWithDrawViewset, \
    ProxyDeviceViewset, ProxyReceiveBankViewset,ProxyCountViewset,ProxyCDatatViewset,ProxyADataViewset,ProxyWDatatViewset

route = DefaultRouter()
route.register(r'user', ProxyUserInfoViewset, base_name="proxy/info")
route.register(r'rateinfo', ProxyRateInfoViewset, base_name="proxy/rateinfo")
route.register(r'order', ProxyOrderInfoViewset, base_name="proxy/order")
route.register(r'withdraw', ProxyWithDrawViewset, base_name="proxy/withdraw")
route.register(r'device', ProxyDeviceViewset, base_name="proxy/device")
route.register(r'receivebankinfo', ProxyReceiveBankViewset, base_name="proxy/receivebankinfo")
route.register(r'count', ProxyCountViewset, base_name="proxy/count")
route.register(r'cdata', ProxyCDatatViewset, base_name="proxy/cdata")
route.register(r'wdata', ProxyWDatatViewset, base_name="proxy/wdata")
route.register(r'adata', ProxyADataViewset, base_name="proxy/adata")
urlpatterns = [
    url(r'^', include(route.urls)),
]
