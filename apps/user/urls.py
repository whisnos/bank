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
from .views import UserInfoViewset,UserOrderViewset,UserWithDrawViewset,UserWithDrawBankViewset,UserCountViewset
route = DefaultRouter()
route.register(r'info', UserInfoViewset, base_name="info")
route.register(r'order', UserOrderViewset, base_name="order")
route.register(r'withdraw', UserWithDrawViewset, base_name="withdraw")
route.register(r'withdrawbank', UserWithDrawBankViewset, base_name="withdrawbank")
route.register(r'count', UserCountViewset, base_name="count")
urlpatterns = [
    url(r'^', include(route.urls)),
]
