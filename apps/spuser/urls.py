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
from .views import AdminProxyViewset,AdminuserProxyViewset,AdminChannelViewset,AdminOrderViewset,AdminWithDrawViewset,AdminNoticeViewset,AdminCountViewset
route = DefaultRouter()
route.register(r'proxy', AdminProxyViewset, base_name="admin/proxy")
route.register(r'user', AdminuserProxyViewset, base_name="admin/user")
route.register(r'channel', AdminChannelViewset, base_name="admin/channel")
route.register(r'order', AdminOrderViewset, base_name="admin/order")
route.register(r'withdraw', AdminWithDrawViewset, base_name="admin/withdraw")
route.register(r'notice', AdminNoticeViewset, base_name="admin/notice")
route.register(r'count', AdminCountViewset, base_name="admin/count")
urlpatterns = [
    url(r'^', include(route.urls)),
]
