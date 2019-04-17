import datetime
import json
import re
import time
from decimal import Decimal

import requests
from django.db.models import Sum, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_renderer_xlsx.renderers import XLSXRenderer
from rest_framework import viewsets, mixins, renderers
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from channel.models import channelInfo
from proxy.filters import ProxyUserFilter, WithDrawFilter, DeviceFilter, ReceiveBankFilter, DeviceChannelFilter
from proxy.models import RateInfo, DeviceInfo, ReceiveBankInfo, DeviceChannelInfo
from proxy.serializers import ProxyUserDetailSerializer, ProxyRateInfoCreateSerializer, ProxyRateInfoDetailSerializer, \
    UpdateRateInfoSerializer, ProxyWithDrawInfoDetailSerializer, \
    ProxyWithDrawInfoUpdateDetailSerializer, ProxyDeviceInfoDetailSerializer, ProxyDeviceUpdateDetailSerializer, \
    ProxyWithDrawInfoCreSerializer, ProxyReceiveBankInfoDetailSerializer, ProxyReceiveBankCreDetailSerializer, \
    ProxyReceiveBankInfoUpdateDetailSerializer, ProxyReceiveBankInfoRetriDetailSerializer, ProxyCountDetailSerializer, \
    ProxyCODataRetrieveSerializer, ProxyCODataSerializer, CallBackOrderUpdateSeralizer, ProxyDChannelDetailSerializer
from spuser.filters import AdminOrderFilter, AdminProxyFilter, LogFilter
from spuser.models import LogInfo
from spuser.serializers import AdminOrderDetailSerializer, OrderChartListSerializer, AdminLogListInfoSerializer, \
    AdminLogInfoSerializer
from trade.models import OrderInfo, WithDrawInfo
from user.models import UserProfile
from user.serializers import UpdateUserInfoSerializer, ProxyUserCreateSerializer

from utils.make_code import make_auth_code, make_uuid_code
from utils.permissions import IsProxyOnly, MakeLogs


class UserListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    page_query_param = 'page'
    max_page_size = 100000


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
        remark=serializer.validated_data.get('remark')
        web_url = self.request.data.get('web_url')
        user = self.get_object()
        log = MakeLogs()
        # 代理 修改 商户
        if add_money:
            user.total_money = '%.2f' % (user.total_money + add_money)
            user.money = '%.2f' % (user.money + add_money)
            # 加日志
            if not remark:
                remark = '无备注！'
            content = '用户：' + str(proxy_user.username) + ' 对 ' + str(
                user.username) + ' 加款 ' + ' 金额 ' + str(add_money) + ' 元。' + ' 备注：' + str(remark)
            log.add_logs('3', content, proxy_user.id)
            # 更新代理余额
            proxy_user.total_money = '%.2f' % (proxy_user.total_money + add_money)
            proxy_user.money = '%.2f' % (proxy_user.money + add_money)
            proxy_user.save()
        if desc_money:
            if desc_money <= user.total_money and proxy_user.total_money >= desc_money:
                user.total_money = '%.2f' % (user.total_money - desc_money)
                user.money = '%.2f' % (user.money - desc_money)
                # 加日志
                if not remark:
                    remark = '无备注！'
                content = '用户：' + str(proxy_user.username) + ' 对 ' + str(
                    user.username) + ' 扣款 ' + ' 金额 ' + str(desc_money) + ' 元。' + ' 备注：' + str(remark)
                log.add_logs('3', content, proxy_user.id)
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


class ProxyOrderInfoViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminOrderFilter
    renderer_classes = (renderers.JSONRenderer, XLSXRenderer, renderers.BrowsableAPIRenderer)
    column_header = {
        'titles': [
            "订单id",
            "创建时间",
            "通道名称",
            "设备名称",
            "用户名",
            "费率",
            "支付状态",
            "订单金额",
            "实际金额",
            "订单号",
            "商户订单号",
            "备注",
            "支付时间",
            "商品名称",
            "所属代理",
            "支付url",
            "收款账号",
            "notify_url",
        ]
    }

    def get_queryset(self):
        return OrderInfo.objects.filter(proxy=self.request.user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
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
            if withdraw_status in [0, 1,2]:
                withdraw_obj.withdraw_status = withdraw_status
                withdraw_obj.receive_time = datetime.datetime.now()
            else:
                code = 400
                resp['msg'] = '修改状态参数错误'
                return Response(data=resp, status=code)
        withdraw_obj.save()
        serializer = ProxyWithDrawInfoDetailSerializer(withdraw_obj)
        return Response(data=serializer.data, status=code)


class ProxyDeviceViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = DeviceFilter

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


class ProxyRealDeviceViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = DeviceChannelFilter


    def get_queryset(self):
        device_q=DeviceInfo.objects.filter(user_id=self.request.user.id)
        did_list=[d.id for d in device_q]
        return DeviceChannelInfo.objects.filter(device_id__in=did_list).order_by('-add_time')

    def get_serializer_class(self):
        return ProxyDChannelDetailSerializer

class ProxyReceiveBankViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_class = ReceiveBankFilter
    search_fields = ('username', 'card_number')
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
    permission_classes = [IsAuthenticated,IsProxyOnly]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter

    def get_queryset(self):
        return UserProfile.objects.filter(proxy_id=self.request.user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        return ProxyCountDetailSerializer


class ProxyWDatatViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    def list(self, request, *args, **kwargs):
        resp = {} # ?s_time=2019-4-12&e_time=2019-4-16
        user_queryset = UserProfile.objects.filter(proxy_id=self.request.user.id)
        user_list=[d.id for d in user_queryset]
        # 总金额
        total_money = user_queryset.aggregate(
            total_money=Sum('total_money')).get('total_money', '0')
        # 可提现
        ke_money = user_queryset.aggregate(
            money=Sum('money')).get('money', '0')
        # 已提现
        withd_queryset = WithDrawInfo.objects.filter(user_id__in=user_list)
        yi_money = withd_queryset.filter(withdraw_status=1).aggregate(
            withdraw_money=Sum('withdraw_money')).get('withdraw_money', '0')
        # 提现中
        zhong_money = withd_queryset.filter(withdraw_status=0).aggregate(
            withdraw_money=Sum('withdraw_money')).get('withdraw_money', '0')

        # 可提现
        resp['ke_money'] = ke_money
        # 已提现
        resp['yi_money'] = yi_money
        # 提现中
        resp['zhong_money'] = zhong_money
        # 总金额
        resp['total_money'] = total_money

        code = 200
        return Response(data=resp, status=code)
class ProxyCDatatViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    def list(self, request, *args, **kwargs):
        resp = {} # ?s_time=2019-4-12&e_time=2019-4-16
        now = datetime.datetime.now()
        # 今天零点
        a_time = (now - datetime.timedelta(hours=now.hour, minutes=now.minute))
        t_time = a_time.strftime('%Y-%m-%d %H:%M')
        te_time = (a_time + datetime.timedelta(hours=23, minutes=59, seconds=59)).strftime(
            '%Y-%m-%d %H:%M')  # .strftime('%Y-%m-%d %H:%M')
        s_time = request.GET.get('start_time', t_time)
        e_time = request.GET.get('end_time', te_time)
        if not s_time or not e_time:
            s_time = t_time
            e_time = te_time
        if not re.match(r'^(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})$', str(s_time)):
            code = 400
            resp['msg'] = '时间格式错误'
            return Response(data=resp, status=code)
        if not re.match(r'^(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})$', str(e_time)):
            code = 400
            resp['msg'] = '时间格式错误'
            return Response(data=resp, status=code)

        order_queryset = OrderInfo.objects.filter(
            add_time__range=(s_time, e_time),proxy=self.request.user.id)  # Q(add_time__gte=s_time) | Q(add_time__lte=e_time)
        all_money = order_queryset.aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        success_money = order_queryset.filter(Q(pay_status=1)|Q(pay_status=3)).aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        all_num = order_queryset.count()
        success_num = order_queryset.filter(Q(pay_status=1)|Q(pay_status=3)).count()

        # user_queryset = UserProfile.objects.filter(proxy_id=self.request.user.id)
        # user_list=[d.id for d in user_queryset]
        # # 总金额
        # total_money = user_queryset.aggregate(
        #     total_money=Sum('total_money')).get('total_money', '0')
        # # 可提现
        # ke_money = user_queryset.aggregate(
        #     money=Sum('money')).get('money', '0')
        # # 已提现
        # withd_queryset = WithDrawInfo.objects.filter(user_id__in=user_list)
        # yi_money = withd_queryset.filter(withdraw_status=1).aggregate(
        #     withdraw_money=Sum('withdraw_money')).get('withdraw_money', '0')
        # # 提现中
        # zhong_money = withd_queryset.filter(withdraw_status=0).aggregate(
        #     withdraw_money=Sum('withdraw_money')).get('withdraw_money', '0')

        # 订单
        resp['all_money'] = all_money
        resp['success_money'] = success_money
        resp['all_num'] = all_num
        resp['success_num'] = success_num
        # # 可提现
        # resp['ke_money'] = ke_money
        # # 已提现
        # resp['yi_money'] = yi_money
        # # 提现中
        # resp['zhong_money'] = zhong_money
        # # 总金额
        # resp['total_money'] = total_money

        code = 200
        return Response(data=resp, status=code)

class ProxyADataViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    def list(self, request, *args, **kwargs):
        resp = {} # ?s_time=2019-4-12&e_time=2019-4-16
        order_queryset = OrderInfo.objects.filter(proxy=self.request.user.id)  # Q(add_time__gte=s_time) | Q(add_time__lte=e_time)
        all_money = order_queryset.aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        success_money = order_queryset.filter(Q(pay_status=1)|Q(pay_status=3)).aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        all_num = order_queryset.count()
        success_num = order_queryset.filter(Q(pay_status=1)|Q(pay_status=3)).count()

        # 订单
        resp['success_money'] = success_money
        resp['all_money'] = all_money
        resp['success_num'] = success_num
        resp['all_num'] = all_num

        code = 200
        return Response(data=resp, status=code)

class ProxyCODataViewset(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    def get_queryset(self):
        return UserProfile.objects.filter(proxy_id=self.request.user.id).order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProxyCODataRetrieveSerializer
        return ProxyCODataSerializer

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        resp = {}  # ?s_time=2019-4-12&e_time=2019-4-16
        now = datetime.datetime.now()
        # 今天零点
        a_time = (now - datetime.timedelta(hours=now.hour, minutes=now.minute))
        t_time = a_time.strftime('%Y-%m-%d %H:%M')
        te_time = (a_time + datetime.timedelta(hours=23, minutes=59, seconds=59)).strftime(
            '%Y-%m-%d %H:%M')  # .strftime('%Y-%m-%d %H:%M')
        s_time = request.GET.get('start_time', t_time)
        e_time = request.GET.get('end_time', te_time)
        if not s_time or not e_time:
            s_time = t_time
            e_time = te_time
        if not re.match(r'^(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})$', str(s_time)):
            code = 400
            resp['msg'] = '时间格式错误'
            return Response(data=resp, status=code)
        if not re.match(r'^(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})$', str(e_time)):
            code = 400
            resp['msg'] = '时间格式错误'
            return Response(data=resp, status=code)
        print('s_time',s_time,e_time)
        order_queryset = OrderInfo.objects.filter(add_time__range=(s_time, e_time),user_id=user.id)  # Q(add_time__gte=s_time) | Q(add_time__lte=e_time)
        print('order_queryset',order_queryset)
        all_money = order_queryset.aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        success_money = order_queryset.filter(Q(pay_status=1)|Q(pay_status=3)).aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        all_num = order_queryset.count()
        success_num = order_queryset.filter(Q(pay_status=1)|Q(pay_status=3)).count()

        # 订单
        resp['success_money'] = success_money
        resp['all_money'] = all_money
        resp['success_num'] = success_num
        resp['all_num'] = all_num

        code = 200
        return Response(data=resp, status=code)

class ProxyCUDataViewset(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated,IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    def get_queryset(self):
        return UserProfile.objects.filter(proxy_id=self.request.user.id).order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProxyCODataRetrieveSerializer
        return ProxyCODataSerializer

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        resp = {}  # ?s_time=2019-4-12&e_time=2019-4-16
        now = datetime.datetime.now()
        # 今天零点
        a_time = (now - datetime.timedelta(hours=now.hour, minutes=now.minute))
        t_time = a_time.strftime('%Y-%m-%d %H:%M')
        te_time = (a_time + datetime.timedelta(hours=23, minutes=59, seconds=59)).strftime(
            '%Y-%m-%d %H:%M')  # .strftime('%Y-%m-%d %H:%M')
        s_time = request.GET.get('start_time', t_time)
        e_time = request.GET.get('end_time', te_time)
        if not s_time or not e_time:
            s_time = t_time
            e_time = te_time
        if not re.match(r'^(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})$', str(s_time)):
            code = 400
            resp['msg'] = '时间格式错误'
            return Response(data=resp, status=code)
        if not re.match(r'^(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})$', str(e_time)):
            code = 400
            resp['msg'] = '时间格式错误'
            return Response(data=resp, status=code)
        print('s_time',s_time,e_time)
        order_queryset = OrderInfo.objects.filter(add_time__range=(s_time, e_time),user_id=user.id)  # Q(add_time__gte=s_time) | Q(add_time__lte=e_time)
        print('order_queryset',order_queryset)
        all_money = order_queryset.aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        success_money = order_queryset.filter(Q(pay_status=1)|Q(pay_status=3)).aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        all_num = order_queryset.count()
        success_num = order_queryset.filter(Q(pay_status=1)|Q(pay_status=3)).count()

        # 订单
        resp['success_money'] = success_money
        resp['all_money'] = all_money
        resp['success_num'] = success_num
        resp['all_num'] = all_num

        code = 200
        return Response(data=resp, status=code)
class ProxyChartViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated, IsProxyOnly)
    serializer_class = OrderChartListSerializer
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    def get_queryset(self):
        return OrderInfo.objects.filter(
            Q(pay_status=1) | Q(pay_status=3),
            add_time__gte=time.strftime('%Y-%m-%d', time.localtime()),proxy=self.request.user.id
        ).order_by('-add_time')


class ProxyCallBackViewset(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.UpdateModelMixin,mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated, IsProxyOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "update":
            return CallBackOrderUpdateSeralizer
        return AdminOrderDetailSerializer

    def get_queryset(self):
        return OrderInfo.objects.filter(proxy=self.request.user.id).order_by('-add_time')

    def update(self, request, *args, **kwargs):
        user = self.request.user
        resp = {'msg': []}
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_obj=self.get_object()
        print('order_obj',order_obj.pay_status)
        if order_obj.pay_status in [2,3]:
            # # 引入日志
            # log = MakeLogs()
            user_queryset = UserProfile.objects.filter(id=order_obj.user_id)
            if user_queryset:
                order_user = user_queryset[0]
                notify_url = order_obj.notify_url
                if not notify_url:
                    order_obj.pay_status = 3
                    order_obj.save()
                    resp['msg'] = '订单处理成功，无效notify_url，通知失败'
                    return Response(data=resp, status=400)

                resp['pay_status'] = order_obj.pay_status
                resp['add_time'] = str(order_obj.add_time)
                resp['pay_time'] = str(order_obj.pay_time)
                resp['real_money'] = str(order_obj.real_money)
                resp['order_id'] = order_obj.order_id
                resp['order_no'] = order_obj.order_no
                resp['remark'] = order_obj.remark
                resp['order_money'] = str(order_obj.order_money)
                r = json.dumps(resp)
                headers = {'Content-Type': 'application/json'}

                if order_obj.pay_status == 3: # 通知失败
                    try:
                        res = requests.post(notify_url, headers=headers, data=r, timeout=10, stream=True)
                        if res.text == 'success':
                            resp['msg'] = '回调成功，成功更改订单状态!'
                            order_obj.pay_status = 1
                            resp['pay_time'] = order_obj.pay_time = datetime.datetime.now()
                            order_obj.save()
                            resp['pay_status'] = order_obj.pay_status
                            # # 加日志
                            # content = '用户：' + str(self.request.user.username) + ' 对订单号: ' + str(
                            #     order_obj.order_no) + ' 强行回调成功'
                            # log.add_logs('1', content, self.request.user.id)
                            return Response(data=resp, status=200)
                        else:
                            # # 加日志
                            # content = '用户：' + str(self.request.user.username) + ' 对订单号: ' + str(
                            #     order_obj.order_no) + ' 强行回调失败，请检查回调地址'
                            # log.add_logs('1', content, self.request.user.id)
                            resp['msg'] = '回调处理，未修改状态，通知失败'
                            return Response(data=resp, status=400)
                    except Exception:
                        # 加日志
                        # content = '用户：' + str(self.request.user.username) + ' 对订单号: ' + str(
                        #     order_obj.order_no) + ' 强行回调失败，请检查回调地址'
                        # log.add_logs('1', content, self.request.user.id)
                        resp['msg'] = '回调异常，订单状态未修改'
                        return Response(data=resp, status=400)
                elif order_obj.pay_status == 2: #订单关闭
                        try:
                            res = requests.post(notify_url, headers=headers, data=r, timeout=10, stream=True)
                            # 更新用户收款
                            order_user.total_money = '%.2f' % (
                                    Decimal(order_user.total_money) + Decimal(order_obj.total_amount))
                            order_user.save()
                            # 代理代理收款
                            user.total_money = '%.2f' % (
                                        Decimal(user.total_money) + Decimal(order_obj.real_money))
                            user.money = '%.2f' % (
                                        Decimal(user.money) + Decimal(order_obj.real_money))
                            user.save()
                            account_num = order_obj.account_num
                            bank_queryset = ReceiveBankInfo.objects.filter(account_num=account_num)
                            if bank_queryset:
                                bank_obj = bank_queryset[0]

                                # 更新商家存钱
                                bank_obj.total_money = '%.2f' % (
                                        Decimal(bank_obj.total_money) + Decimal(order_obj.real_money))
                                bank_obj.last_time = datetime.datetime.now()
                                bank_obj.save()

                            else:
                                resp['mark'] = '不存在有效银行卡，金额未添加到银行卡'

                            if res.text == 'success':
                                resp['pay_status'] = 1
                                resp['pay_time'] = order_obj.pay_time = datetime.datetime.now()
                                order_obj.pay_status = 1
                                order_obj.save()
                                # 加日志
                                # content = '用户：' + str(self.request.user.username) + ' 对订单号: ' + str(
                                #     order_obj.order_no) + ' 强行回调成功'
                                # log.add_logs('1', content, self.request.user.id)

                                resp['msg'] = '回调成功，已自动加款，金额:' + str(order_obj.total_amount)
                                return Response(data=resp, status=200)
                            else:
                                resp['pay_status'] = 3
                                resp['pay_time'] = order_obj.pay_time = datetime.datetime.now()
                                order_obj.pay_status = 3
                                order_obj.save()
                                # 日志
                                # content = '用户：' + str(self.request.user.username) + ' 对订单号: ' + str(
                                #     order_obj.order_no) + ' 强行回调失败，请检查回调地址'
                                # log.add_logs('1', content, self.request.user.id)
                                resp['msg'] = '回调处理，响应异常，通知失败'
                                return Response(data=resp, status=400)
                        except Exception:
                            resp['pay_status'] = 3
                            resp['pay_time'] = order_obj.pay_time = datetime.datetime.now()
                            order_obj.pay_status = 3
                            order_obj.save()
                            # 更新用户收款
                            order_user.total_money = '%.2f' % (
                                    Decimal(order_user.total_money) + Decimal(order_obj.real_money))
                            order_user.save()

                            account_num = order_obj.account_num
                            bank_queryset = ReceiveBankInfo.objects.filter(account_num=account_num)
                            if bank_queryset:
                                bank_obj = bank_queryset[0]

                                # 更新商家存钱
                                bank_obj.total_money = '%.2f' % (
                                        Decimal(bank_obj.total_money) + Decimal(order_obj.real_money))
                                bank_obj.last_time = datetime.datetime.now()
                                bank_obj.save()

                            else:
                                resp['mark'] = '不存在有效银行卡，金额未添加到银行卡'
                            # 日志
                            # content = '用户：' + str(self.request.user.username) + ' 对订单号: ' + str(
                            #     order_obj.order_no) + ' 强行回调失败，请检查回调地址'
                            # log.add_logs('1', content, self.request.user.id)
                            resp['msg'] = '回调处理，加款成功金额:%s，通知失败' % (str(order_obj.total_amount))
                            return Response(data=resp, status=400)
            code = 400
            resp['msg'] = '代理账号不存在'
            return Response(data=resp, status=code)
        code = 400
        resp['msg'] = '操作状态不对'
        return Response(data=resp, status=code)

class ProxyLogsViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,IsProxyOnly )
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = LogFilter

    def get_queryset(self):
       u_list=[u.id for u in UserProfile.objects.filter(proxy_id=self.request.user.id)]
       return LogInfo.objects.filter(user_id__in=u_list).order_by('-add_time')


    def get_serializer_class(self):
        if self.action == 'list':
            return AdminLogListInfoSerializer
        else:
            return AdminLogInfoSerializer