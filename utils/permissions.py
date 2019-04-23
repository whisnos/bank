from rest_framework import permissions


# from user.models import OperateLog
from rest_framework.authentication import BaseAuthentication
from rest_framework_jwt.authentication import BaseJSONWebTokenAuthentication, JSONWebTokenAuthentication
from rest_framework_jwt.serializers import jwt_get_username_from_payload

from proxy.models import DeviceInfo
from spuser.models import LogInfo


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_superuser


# login 增加字段
def jwt_response_payload_handler(token, user=None, request=None):
    """为返回的结果添加用户相关信息"""
    if not user.level:
        user.level = None
    if request.META.get('HTTP_X_FORWARDED_FOR', ''):
        print('HTTP_X_FORWARDED_FOR')
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
    else:
        print('REMOTE_ADDR')
        ip = request.META.get('REMOTE_ADDR', '')
    # 引入日志
    log = MakeLogs()
    content = '用户：' + str(user.username) + ' 登录ip为：' + str(ip)
    log.add_logs('0', content, user.id)
    return {
        'token': token,
        'username': user.username,
        'level': user.level,
        # 'id': user.id,
        # 'auth_code': user.auth_code,
    }


class MakeLogs(object):
    def add_logs(self,log_type,content,user_id):
        log_obj = LogInfo()
        log_obj.log_type = log_type
        log_obj.content = content
        log_obj.user_id = user_id
        log_obj.save()
        return True
class IsProxyOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_permission(self, request, view):
        if request.user.level == 2:
            return True
        else:
            return False

class IsUserOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_permission(self, request, view):
        if request.user.level == 3:
            return True
        else:
            return False
class IsDeviceOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_permission(self, request, view):
        # print('self',dir(self))
        # print('2',dir(request),request.data)
        username=request.data.get('username')
        d_queryset=DeviceInfo.objects.filter(device_name=username)
        if d_queryset:
            return True
        else:
            return False

from rest_framework import exceptions
from django.utils.translation import ugettext as _
class XXXToken(JSONWebTokenAuthentication,BaseJSONWebTokenAuthentication):
    def authenticate_credentials(self, payload):
        """
        Returns an active user that matches the payload's user id and email.
        """
        # User = get_user_model()
        # User = get_deviceinfo_model()
        User = DeviceInfo
        username = jwt_get_username_from_payload(payload)

        if not username:
            msg = _('Invalid payload.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            user = User.objects.get_by_natural_key(username)
        except User.DoesNotExist:
            msg = _('Invalid signature.')
            raise exceptions.AuthenticationFailed(msg)

        if not user.is_active:
            msg = _('User account is disabled.')
            raise exceptions.AuthenticationFailed(msg)

        return user

