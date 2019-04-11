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
from .views import AdminProxyViewset,AdminuserProxyViewset,AdminChannelViewset,AdminOrderViewset,AdminWithDrawViewset,AdminNoticeViewset
route = DefaultRouter()
route.register(r'proxy', AdminProxyViewset, base_name="proxy")
route.register(r'user', AdminuserProxyViewset, base_name="user")
route.register(r'channel', AdminChannelViewset, base_name="channel")
route.register(r'order', AdminOrderViewset, base_name="order")
route.register(r'withdraw', AdminWithDrawViewset, base_name="withdraw")
route.register(r'notice', AdminNoticeViewset, base_name="notice")
urlpatterns = [
    url(r'^', include(route.urls)),
]
