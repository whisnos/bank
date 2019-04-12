from decimal import Decimal

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from channel.models import channelInfo
from proxy.filters import ProxyUserFilter, WithDrawFilter, DeviceFilter, ReceiveBankFilter
from proxy.models import RateInfo, DeviceInfo, ReceiveBankInfo
from proxy.serializers import ProxyUserDetailSerializer, ProxyRateInfoCreateSerializer, ProxyRateInfoDetailSerializer, \
    UpdateRateInfoSerializer, ProxyWithDrawInfoDetailSerializer, \
    ProxyWithDrawInfoUpdateDetailSerializer, ProxyDeviceInfoDetailSerializer, ProxyDeviceUpdateDetailSerializer, \
    ProxyWithDrawInfoCreSerializer, ProxyReceiveBankInfoDetailSerializer, ProxyReceiveBankCreDetailSerializer, \
    ProxyReceiveBankInfoUpdateDetailSerializer, ProxyReceiveBankInfoRetriDetailSerializer
from spuser.filters import AdminOrderFilter, AdminProxyFilter
from spuser.serializers import AdminOrderDetailSerializer, AdminCountDetailSerializer
from trade.models import OrderInfo, WithDrawInfo
from user.models import UserProfile
from user.serializers import UpdateUserInfoSerializer, ProxyUserCreateSerializer

from utils.make_code import make_auth_code, make_md5, make_uuid_code
from utils.permissions import IsOwnerOrReadOnly, IsProxyOnly


class UserListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    page_query_param = 'page'
    max_page_size = 100


class ProxyUserInfoViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                           mixins.CreateModelMixin,
                           mixins.UpdateModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = ProxyUserFilter

    def get_queryset(self):
        user = self.request.user
        return UserProfile.objects.filter(proxy_id=user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'update':
            return UpdateUserInfoSerializer
        elif self.action == 'create':
            return ProxyUserCreateSerializer
        return ProxyUserDetailSerializer

    def create(self, request, *args, **kwargs):
        proxy_user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        del validated_data['password2']
        user = UserProfile.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.uid = make_uuid_code()
        user.auth_code = make_auth_code()
        user.is_active = False
        user.proxy_id = proxy_user.id
        user.save()
        code = 200
        serializer = ProxyUserDetailSerializer(user)
        return Response(data=serializer.data, status=code)

    def update(self, request, *args, **kwargs):
        proxy_user = self.request.user
        code = 201
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth_code = self.request.data.get('auth_code')
        add_money=serializer.validated_data.get('add_money')
        desc_money=serializer.validated_data.get('desc_money')
        web_url = self.request.data.get('web_url')
        user = self.get_object()
        # 代理 修改 商户
        if add_money:
            user.total_money = '%.2f' % (user.total_money + add_money)
            user.money = '%.2f' % (user.money + add_money)
            # # 加日志
            # if not ramark_info:
            #     ramark_info = '无备注！'
            # content = '用户：' + str(self.request.user.username) + ' 对 ' + str(
            #     user.username) + ' 加款 ' + ' 金额 ' + str(add_money) + ' 元。' + ' 备注：' + str(ramark_info)
            # log.add_logs('3', content, self.request.user.id)
            # 更新代理余额
            proxy_user.total_money = '%.2f' % (proxy_user.total_money + add_money)
            proxy_user.money = '%.2f' % (proxy_user.money + add_money)
            proxy_user.save()
        if desc_money:
            if desc_money <= user.total_money and proxy_user.total_money >= desc_money:
                user.total_money = '%.2f' % (user.total_money - desc_money)
                user.money = '%.2f' % (user.money - desc_money)
                # # 加日志
                # if not ramark_info:
                #     ramark_info = '无备注！'
                # content = '用户：' + str(self.request.user.username) + ' 对 ' + str(
                #     user.username) + ' 扣款 ' + ' 金额 ' + str(minus_money) + ' 元。' + ' 备注：' + str(ramark_info)
                # log.add_logs('3', content, self.request.user.id)
                # 更新代理余额
                proxy_user.total_money = '%.2f' % (proxy_user.total_money - desc_money)
                proxy_user.money = '%.2f' % (proxy_user.money - desc_money)
                proxy_user.save()
            else:
                code = 404
        if web_url:
            user.web_url = web_url
        if auth_code:
            user.auth_code = make_auth_code()
        user.save()
        serializer = ProxyUserDetailSerializer(user)
        return Response(data=serializer.data, status=code)


class ProxyRateInfoViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                           mixins.CreateModelMixin,
                           mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    def make_userlist(self):
        user_list = [users.id for users in UserProfile.objects.filter(proxy_id=self.request.user.id)]
        return user_list

    def get_queryset(self):
        # user = self.request.user
        user_list = self.make_userlist()
        return RateInfo.objects.filter(user_id__in=user_list).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'update':
            return UpdateRateInfoSerializer
        elif self.action == 'create':
            return ProxyRateInfoCreateSerializer
        return ProxyRateInfoDetailSerializer


    def create(self, request, *args, **kwargs):
        resp = {'msg': []}
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proxy_user = self.request.user
        userid = serializer.validated_data.get('user_id')
        channel_id = serializer.validated_data.get('channel_id')
        if not channelInfo.objects.filter(id=channel_id):
            code = 400
            resp['msg'] = '操作通道不存在'
            return Response(data=resp, status=code)
        if userid:
            user_list = self.make_userlist()
            if int(userid) in user_list:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                validated_data = serializer.validated_data
                user = RateInfo.objects.create(**validated_data)
                code = 200
                resp['msg'] = '创建成功'
                serializer = ProxyRateInfoCreateSerializer(user)
                return Response(data=serializer.data, status=code)
            else:
                code = 400
                resp['msg'] = '操作对象不存在'
                return Response(data=resp, status=code)
        else:
            code = 400
            resp['msg'] = 'user_id无效参数'
            return Response(data=resp, status=code)

    def update(self, request, *args, **kwargs):
        resp = {'msg': []}
        proxy_user = self.request.user
        rate_obj = self.get_object()
        code = 201
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rate = self.request.data.get('rate', '')
        is_map = serializer.validated_data.get('is_map', '')
        mapid = self.request.data.get('mapid', '')
        # 代理 修改 商户
        if proxy_user.level == 2:
            if rate:
                rate_obj.rate = rate
                rate_obj.save()
            if str(is_map):
                if is_map:
                    if mapid:
                        rate_obj.is_map = is_map
                        rate_obj.mapid = mapid
                    else:
                        code = 400
                        resp['msg'] = '映射ip必传'
                        return Response(data=resp, status=code)
                if is_map == False:
                    rate_obj.is_map = is_map
            rate_obj.save()
            serializer = ProxyRateInfoDetailSerializer(rate_obj)
            return Response(data=serializer.data, status=code)
        code = 403
        resp['msg'] = '没有操作权限'
        return Response(data=resp, status=code)


class ProxyOrderInfoViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminOrderFilter

    def make_userlist(self):
        user_list = [users.id for users in UserProfile.objects.filter(proxy_id=self.request.user.id)]
        return user_list

    def get_queryset(self):
        user_list = self.make_userlist()
        return OrderInfo.objects.filter(user_id__in=user_list).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        # return ProxyOrderInfoDetailSerializer
        return AdminOrderDetailSerializer



class ProxyWithDrawViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = WithDrawFilter

    def make_userlist(self):
        user_list = [users.id for users in UserProfile.objects.filter(proxy_id=self.request.user.id)]
        return user_list

    def get_queryset(self):
        user_list = self.make_userlist()
        return WithDrawInfo.objects.filter(user_id__in=user_list).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'update':
            return ProxyWithDrawInfoUpdateDetailSerializer
        return ProxyWithDrawInfoDetailSerializer


    def update(self, request, *args, **kwargs):
        resp = {'msg': []}
        withdraw_obj = self.get_object()
        code = 201
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        withdraw_status = serializer.validated_data.get('withdraw_status', '')
        remark = self.request.data.get('remark', '')
        # 代理 修改 商户
        if remark:
            withdraw_obj.remark = remark
        if str(withdraw_status):
            if withdraw_status in [0, 1]:
                withdraw_obj.withdraw_status = withdraw_status
            else:
                code = 400
                resp['msg'] = '修改状态参数错误'
                return Response(data=resp, status=code)
        serializer = ProxyWithDrawInfoDetailSerializer(withdraw_obj)
        return Response(data=serializer.data, status=code)


class ProxyDeviceViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = DeviceFilter

    def make_userlist(self):
        user_list = [users.id for users in UserProfile.objects.filter(proxy_id=self.request.user.id)]
        return user_list

    def get_queryset(self):
        return DeviceInfo.objects.filter(user_id=self.request.user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'update':
            return ProxyDeviceUpdateDetailSerializer
        elif self.action == 'create':
            return ProxyWithDrawInfoCreSerializer
        return ProxyDeviceInfoDetailSerializer


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        del validated_data['password2']
        device_obj = DeviceInfo.objects.create(**validated_data)
        code = 200
        serializer = ProxyDeviceInfoDetailSerializer(device_obj)
        return Response(data=serializer.data, status=code)

    def update(self, request, *args, **kwargs):
        device_obj = self.get_object()
        code = 201
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_active = serializer.validated_data.get('is_active', '')
        # 代理 修改 商户
        if str(is_active):
            device_obj.is_active = is_active
            device_obj.save()
        serializer = ProxyDeviceInfoDetailSerializer(device_obj)
        return Response(data=serializer.data, status=code)


class ProxyReceiveBankViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = ReceiveBankFilter

    def get_queryset(self):
        return ReceiveBankInfo.objects.filter(user_id=self.request.user.id).order_by(
            '-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'update':
            return ProxyReceiveBankInfoUpdateDetailSerializer
        elif self.action == 'create':
            return ProxyReceiveBankCreDetailSerializer
        elif self.action == 'retrieve':
            return ProxyReceiveBankInfoRetriDetailSerializer
        return ProxyReceiveBankInfoDetailSerializer


    def update(self, request, *args, **kwargs):
        resp = {'msg': []}
        proxy_user = self.request.user
        # 代理 修改 商户
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        device_list = [device.id for device in DeviceInfo.objects.filter(user_id=proxy_user.id)]
        deviceid = serializer.validated_data.get('device')
        if deviceid not in device_list:
            code = 403
            resp['msg'] = '绑定的设备不存在'
            return Response(data=resp, status=code)
        receivebank_obj=serializer.save()
        code = 201
        serializer = ProxyReceiveBankInfoDetailSerializer(receivebank_obj)
        return Response(data=serializer.data, status=code)

    def create(self, request, *args, **kwargs):
        resp = {'msg': []}
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proxy_user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device_list = [device.id for device in DeviceInfo.objects.filter(user_id=proxy_user.id)]
        if serializer.validated_data.get('device', '') in device_list:
            receivebank_obj = serializer.save()
            code = 200
            serializer = ProxyReceiveBankInfoDetailSerializer(receivebank_obj)
            return Response(data=serializer.data, status=code)
        else:
            code = 400
            resp['msg'] = '绑定的设备不存在'
            return Response(data=resp, status=code)

class ProxyCountViewset(mixins.ListModelMixin, viewsets.GenericViewSet,mixins.RetrieveModelMixin):
    permission_classes = [IsProxyOnly]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter

    def get_queryset(self):
        return UserProfile.objects.filter(level=3).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        return AdminCountDetailSerializer