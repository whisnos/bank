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
from .views import UserInfoViewset, UserOrderViewset, UserWithDrawViewset, UserWithDrawBankViewset, UserCountViewset, \
    UserCDataViewset, UserADataViewset, UserWDataViewset, UserCODataViewset, UserChartViewset, UserLogsViewset

route = DefaultRouter()
route.register(r'info', UserInfoViewset, base_name="info")
route.register(r'order', UserOrderViewset, base_name="order")
route.register(r'withdraw', UserWithDrawViewset, base_name="withdraw")
route.register(r'withdrawbank', UserWithDrawBankViewset, base_name="withdrawbank")
route.register(r'count', UserCountViewset, base_name="count")
route.register(r'cdata', UserCDataViewset, base_name="cdata")
route.register(r'wdata', UserWDataViewset, base_name="wdata")
route.register(r'adata', UserADataViewset, base_name="adata")
route.register(r'codata', UserCODataViewset, base_name="codata")
route.register(r'chart', UserChartViewset, base_name="chart")
route.register(r'logs', UserLogsViewset, base_name="logs")
urlpatterns = [
    url(r'^', include(route.urls)),
]
