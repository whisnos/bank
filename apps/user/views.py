import base64
import codecs
import datetime
import json
import random
import re
import time
from decimal import Decimal

import jwt
import requests
from django.contrib.auth.backends import ModelBackend
from django.db.models import Sum, Q
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from drf_renderer_xlsx.renderers import XLSXRenderer
from rest_framework import viewsets, mixins, views, renderers
# Create your views here.
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler

from bank.settings import CLOSE_TIME, FONT_DOMAIN, ALIPAY_DEBUG, APP_NOTIFY_URL
from channel.models import channelInfo, AlipayInfo
from nsm.cron import callback
from proxy.filters import WithDrawFilter, WithDrawBankFilter
from proxy.models import ReceiveBankInfo, DeviceInfo, RateInfo
from proxy.views import UserListPagination
from spuser.filters import AdminOrderFilter, AdminProxyFilter, LogFilter
from spuser.models import LogInfo
from spuser.serializers import OrderChartListSerializer, AdminLogListInfoSerializer, AdminLogInfoSerializer
from trade.models import OrderInfo, WithDrawInfo, WithDrawBankInfo
from user.models import UserProfile, Google2Auth
from user.serializers import UserDetailSerializer, UserOrderListSerializer, \
    UserWithDrawListSerializer, UserWithDrawCreateSerializer, UserWithDrawBankListSerializer, \
    UserWithDrawBankCreateSerializer, UpdateOnlyUserInfoSerializer, UserCountDetailSerializer, \
    UserCODataSerializer, GoogleOnlyUserInfoSerializer
from utils.alipay import AliPay
from utils.make_code import make_auth_code, make_md5, generate_order_no, make_short_code
from utils.pay import MakePay
from utils.permissions import IsUserOnly, MakeLogs


class CustomModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, type=None, **kwargs):
        print(999)
        '''if request.META.get('HTTP_X_FORWARDED_FOR', ''):
            print('HTTP_X_FORWARDED_FOR')
            ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
        else:
            print('REMOTE_ADDR')
            ip = request.META.get('REMOTE_ADDR', '')
        '''
        # print('request',dir(self))
        # if request.META.get('HTTP_X_FORWARDED_FOR', ''):
        #     print('HTTP_X_FORWARDED_FOR')
        #     ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
        # else:
        #     ip = request.META.get('REMOTE_ADDR', '')
        #     print('REMOTE_ADDR',ip)
        user = UserProfile.objects.filter(username=username).first() or DeviceInfo.objects.filter(
            device_name=username).first()
        try:
            if user.level:
                if user.check_password(password):
                    return user
                else:
                    print(666)
                    return None
        except Exception as e:
            try:
                if user.is_active:
                    if user.password == password:
                        print('设备登录成功', user.id)
                        userid = user.user_id
                        user1 = UserProfile.objects.get(id=userid)
                        return user1
                return None
            except Exception as e:
                return None


class UserInfoViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin):
    permission_classes = (IsAuthenticated, IsUserOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    def get_queryset(self):
        user = self.request.user
        return UserProfile.objects.filter(id=user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'update':
            return UpdateOnlyUserInfoSerializer
        return UserDetailSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.request.user
        code = 201
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = self.request.data.get('password')
        password2 = self.request.data.get('password2')
        auth_code = serializer.validated_data.get('auth_code')
        original_safe_code = self.request.data.get('original_safe_code')
        safe_code = self.request.data.get('safe_code')
        safe_code2 = self.request.data.get('safe_code2')
        # tuoxie001 修改自己
        if password:
            if password == password2:
                user.set_password(password)
            elif password != password2:
                code = 400
        if auth_code:
            user.auth_code = make_auth_code()
        if original_safe_code:
            if make_md5(original_safe_code) == user.safe_code:
                if safe_code == safe_code2:
                    if safe_code:
                        print('tuoxie001修改操作密码中..........')
                        safe_code = make_md5(safe_code)
                        self.request.user.safe_code = safe_code
                else:
                    code = 400
            else:
                code = 400
        user.save()
        serializer = UserDetailSerializer(user)
        return Response(data=serializer.data, status=code)


class UserOrderViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated, IsUserOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminOrderFilter
    renderer_classes = (renderers.JSONRenderer, XLSXRenderer, renderers.BrowsableAPIRenderer)
    column_header = {
        'titles': [
            "订单id",
            "支付时间",
            "创建时间",
            "收款账号",
            "费率",
            "支付状态",
            "订单金额",
            "实际金额",
            "订单号",
            "商户订单号",
            "备注",
            "商品名称",
            "所属代理",
            "支付url",
            "notify_url",
            "通道",
            "用户",
            "设备",

        ]
    }

    def get_queryset(self):
        user = self.request.user
        return OrderInfo.objects.filter(user_id=user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        # if self.action == 'update':
        #     return UpdateUserInfoSerializer
        return UserOrderListSerializer


import pyotp


def Google_Verify_Result(secret_key, verifycode):
    t = pyotp.TOTP(secret_key)
    result = t.verify(verifycode, valid_window=1)  # 对输入验证码进行校验，正确返回True
    res = result if result is True else False
    print("ret:", res)
    return res


class UserWithDrawViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                          mixins.CreateModelMixin):
    permission_classes = (IsAuthenticated, IsUserOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = WithDrawFilter

    def get_queryset(self):
        user = self.request.user
        return WithDrawInfo.objects.filter(user_id=user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'create':
            return UserWithDrawCreateSerializer
        return UserWithDrawListSerializer

    def create(self, request, *args, **kwargs):
        resp = {'msg': []}
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proxy_user = self.request.user
        validated_data = serializer.validated_data
        withdraw_no = generate_order_no(proxy_user.id)
        validated_data['withdraw_no'] = withdraw_no
        bankid = validated_data.get('bank')
        safe_code = validated_data.get('safe_code')
        googel_code = validated_data.get('googel_code')
        if proxy_user.is_google:
            try:
                # 判断用户是否已经绑定Google令牌
                key = Google2Auth.objects.get(user_id=self.request.user.id).key
            except:
                raise Http404("未绑定令牌")
            if not Google_Verify_Result(key, googel_code):
                # 验证令牌
                return Response({"msg": "令牌失效"}, status=400)

        if make_md5(safe_code) == proxy_user.safe_code:
            with_banklist = [wd.id for wd in WithDrawBankInfo.objects.filter(user_id=proxy_user.id)]
            if bankid in with_banklist:
                # 更新商户余额
                withdraw_money = validated_data.get('withdraw_money')
                proxy_user.money = '%.2f' % (
                        Decimal(proxy_user.money) - Decimal(validated_data.get('withdraw_money', '')))
                # 更新代理余额
                daili_queryset = UserProfile.objects.filter(id=proxy_user.proxy_id)
                if daili_queryset:
                    daili_obj = daili_queryset[0]
                    daili_obj.money = '%.2f' % (
                            Decimal(daili_obj.money) - Decimal(validated_data.get('withdraw_money', '')))

                    proxy_user.save()
                    daili_obj.save()
                    # 引入日志
                    log = MakeLogs()
                    content = '用户：' + str(proxy_user.username) + '创建提现_' + '订单号_ ' + str(withdraw_no) + '  金额 ' + str(
                        withdraw_money) + ' 元'
                    log.add_logs('2', content, proxy_user.id)
                    bank_queryset = WithDrawBankInfo.objects.filter(id=bankid)
                    if bank_queryset:
                        bank_obj = bank_queryset[0]
                        validated_data['bank'] = bank_obj
                        del validated_data['safe_code']
                        del validated_data['googel_code']
                        withdraw_obj = WithDrawInfo.objects.create(**validated_data)
                        code = 200
                        resp['msg'] = '创建成功'
                        serializer = UserWithDrawListSerializer(withdraw_obj)
                        return Response(data=serializer.data, status=code)
                    else:
                        code = 400
                        resp['msg'] = '创建失败,不存在代理收款银行卡'
                        return Response(data=resp, status=code)
                else:
                    code = 400
                    resp['msg'] = '创建失败'
                    return Response(data=resp, status=code)
            else:
                code = 400
                resp['msg'] = '绑定的银行卡id不存在'
                return Response(data=resp, status=code)
        else:
            code = 400
            resp['msg'] = '操作密码错误'
            return Response(data=resp, status=code)


class UserWithDrawBankViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                              mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, IsUserOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = WithDrawBankFilter

    def get_queryset(self):
        user = self.request.user
        return WithDrawBankInfo.objects.filter(user_id=user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'create':
            return UserWithDrawBankCreateSerializer
        elif self.action == 'update':
            return UserWithDrawBankCreateSerializer
        return UserWithDrawBankListSerializer


class UserCountViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = [IsAuthenticated, IsUserOnly]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter

    def get_queryset(self):
        return UserProfile.objects.filter(id=self.request.user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        return UserCountDetailSerializer


class UserWDataViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAuthenticated, IsUserOnly,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    def list(self, request, *args, **kwargs):
        resp = {}  # ?s_time=2019-4-12&e_time=2019-4-16

        user_queryset = UserProfile.objects.filter(id=self.request.user.id)
        # 总金额
        total_money = user_queryset.aggregate(
            total_money=Sum('total_money')).get('total_money')
        # 可提现
        ke_money = user_queryset.aggregate(
            money=Sum('money')).get('money')
        # 已提现
        withd_queryset = WithDrawInfo.objects.filter(user_id=self.request.user.id)
        yi_money = withd_queryset.filter(withdraw_status=1).aggregate(
            withdraw_money=Sum('withdraw_money')).get('withdraw_money')
        # 提现中
        zhong_money = withd_queryset.filter(withdraw_status=0).aggregate(
            withdraw_money=Sum('withdraw_money')).get('withdraw_money')
        if not total_money:
            total_money = 0
        if not ke_money:
            ke_money = 0
        if not yi_money:
            yi_money = 0
        if not zhong_money:
            zhong_money = 0
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


class UserCDataViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAuthenticated, IsUserOnly,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    def list(self, request, *args, **kwargs):
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

        order_queryset = OrderInfo.objects.filter(
            add_time__range=(s_time, e_time),
            user_id=self.request.user.id)  # Q(add_time__gte=s_time) | Q(add_time__lte=e_time)
        all_money = order_queryset.aggregate(
            real_money=Sum('real_money')).get('real_money')

        success_money = order_queryset.filter(Q(pay_status=1) | Q(pay_status=3)).aggregate(
            real_money=Sum('real_money')).get('real_money')
        all_num = order_queryset.count()
        order_queryset = order_queryset.filter(Q(pay_status=1) | Q(pay_status=3))
        success_num = order_queryset.count()
        service_money = order_queryset.aggregate(
            service_money=Sum('service_money')).get('service_money')

        if not all_money:
            all_money = 0
        if not success_money:
            success_money = 0
        if not service_money:
            service_money = 0

        # user_queryset = UserProfile.objects.filter(id=self.request.user.id)
        # # 总金额
        # total_money = user_queryset.aggregate(
        #     total_money=Sum('total_money')).get('total_money', '0')
        # # 可提现
        # ke_money = user_queryset.aggregate(
        #     money=Sum('money')).get('money', '0')
        # # 已提现
        # withd_queryset = WithDrawInfo.objects.filter(id=self.request.user.id)
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
        resp['service_money'] = service_money
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


class UserADataViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAuthenticated, IsUserOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    def list(self, request, *args, **kwargs):
        resp = {}  # ?s_time=2019-4-12&e_time=2019-4-16
        order_queryset = OrderInfo.objects.filter(
            user_id=self.request.user.id)  # Q(add_time__gte=s_time) | Q(add_time__lte=e_time)
        all_money = order_queryset.aggregate(
            real_money=Sum('real_money')).get('real_money')
        success_money = order_queryset.filter(Q(pay_status=1) | Q(pay_status=3)).aggregate(
            real_money=Sum('real_money')).get('real_money')
        all_num = order_queryset.count()
        success_num = order_queryset.filter(Q(pay_status=1) | Q(pay_status=3)).count()
        if not all_money:
            all_money = 0
        if not success_money:
            all_money = 0
        # 订单
        resp['success_money'] = success_money
        resp['all_money'] = all_money
        resp['success_num'] = success_num
        resp['all_num'] = all_num

        code = 200
        return Response(data=resp, status=code)


class GetPayView(views.APIView):
    def post(self, request):
        processed_dict = {}
        resp = {'msg': '操作成功'}
        for key, value in request.data.items():
            processed_dict[key] = value
        uid = processed_dict.get('uid', '')
        real_money = order_money = processed_dict.get('money', '')
        remark = processed_dict.get('remark', '')
        order_id = processed_dict.get('order_id', '')
        key = processed_dict.get('key', '')
        return_url = processed_dict.get('return_url', '')
        notify_url = processed_dict.get('notify_url', '')
        channel = processed_dict.get('channel', '')
        plat_type = processed_dict.get('plat_type', '1')
        print('plat_type', plat_type)
        # if not str(real_money) > '1':
        #     resp['msg'] = '金额必须大于1'
        #     return Response(resp, status=404)
        if not order_id:
            resp['msg'] = '请填写订单号~~'
            return Response(resp, status=404)
        if not return_url:
            resp['msg'] = '请填写正确跳转url~~'
            return Response(resp, status=404)
        if not notify_url:
            resp['msg'] = '请填写正确回调url~~'
            return Response(resp, status=404)
        user_queryset = UserProfile.objects.filter(uid=uid, is_active=True)
        if not user_queryset:
            resp['msg'] = 'uid或者auth_code错误，请重试~~'
            return Response(resp, status=404)
        if not re.match(r'(^[1-9]([0-9]{1,4})?(\.[0-9]{1,2})?$)|(^(0){1}$)|(^[0-9]\.[0-9]([0-9])?$)',
                        str(real_money)):
            resp['msg'] = '金额输入错误，请重试~~0.01到5万间'
            return Response(resp, status=404)
        # 识别出 用户
        user = user_queryset[0]
        auth_code = user.auth_code
        # 加密 uid + auth_code + real_money + notify_url + order_id
        new_temp = str(str(uid) + str(auth_code) + str(real_money) + str(notify_url) + str(order_id))
        my_key = make_md5(new_temp)
        if key == my_key:
            # 关闭超时订单
            now_time = datetime.datetime.now() - datetime.timedelta(minutes=CLOSE_TIME)
            OrderInfo.objects.filter(pay_status=0, add_time__lte=now_time).update(
                pay_status=2)
            pay = MakePay(user, order_money, real_money, channel, remark, order_id, notify_url, plat_type, return_url)
            resp = pay.choose_pay()
            return Response(resp, status=200)
        resp['msg'] = 'key匹配错误'
        return Response(resp, status=400)


class UserCODataViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAuthenticated, IsUserOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    def get_queryset(self):
        return UserProfile.objects.filter(id=self.request.user.id).order_by('-add_time')

    def get_serializer_class(self):
        return UserCODataSerializer

    def list(self, request, *args, **kwargs):
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
        if not re.match(r'(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})', str(s_time)):
            code = 400
            resp['msg'] = '时间格式错误'
            return Response(data=resp, status=code)
        if not re.match(r'(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})', str(e_time)):
            code = 400
            resp['msg'] = '时间格式错误'
            return Response(data=resp, status=code)
        order_queryset = OrderInfo.objects.filter(add_time__range=(s_time, e_time),
                                                  user_id=self.request.user.id)  # Q(add_time__gte=s_time) | Q(add_time__lte=e_time)
        all_money = order_queryset.aggregate(
            real_money=Sum('real_money')).get('real_money')
        success_money = order_queryset.filter(Q(pay_status=1) | Q(pay_status=3)).aggregate(
            real_money=Sum('real_money')).get('real_money')
        all_num = order_queryset.count()
        success_num = order_queryset.filter(Q(pay_status=1) | Q(pay_status=3)).count()
        if not all_money:
            all_money = 0
        if not success_money:
            all_money = 0
        # 订单
        resp['success_money'] = success_money
        resp['all_money'] = all_money
        resp['success_num'] = success_num
        resp['all_num'] = all_num

        code = 200
        return Response(data=resp, status=code)


class UserChartViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated, IsUserOnly)
    serializer_class = OrderChartListSerializer
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    def get_queryset(self):
        return OrderInfo.objects.filter(
            Q(pay_status=1) | Q(pay_status=3),
            add_time__gte=time.strftime('%Y-%m-%d', time.localtime()), user_id=self.request.user.id
        ).order_by('-add_time')


@csrf_exempt
def test(request):
    print('接收到的信息', request.body)
    # callback()
    return HttpResponse(status=200, content='success')


class UserLogsViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, IsUserOnly)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = LogFilter

    def get_queryset(self):
        return LogInfo.objects.filter(user_id=self.request.user.id).order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'list':
            return AdminLogListInfoSerializer
        else:
            return AdminLogInfoSerializer


def get_info(request):
    order_id = request.GET.get('id')
    resp = {'msg': []}
    if order_id:
        order_queryset = OrderInfo.objects.filter(id=order_id)
        code = 200
        if order_queryset:
            print(order_queryset.query)
            resp['msg'] = '获取成功'
            resp['money'] = order_queryset[0].order_money
            resp['pay_url'] = order_queryset[0].pay_url
        else:
            resp['msg'] = '不存在相应订单号'
            code = 400
    else:
        resp['msg'] = '不存在相应订单号'
        code = 400
    return JsonResponse(data=resp, status=code)


class QueryOrderView(views.APIView):
    def post(self, request):
        processed_dict = {}
        resp = {'msg': '订单不存在'}
        for key, value in request.data.items():
            processed_dict[key] = value
        uid = processed_dict.get('uid', '')
        order_no = processed_dict.get('order_no', '')
        user_queryset = UserProfile.objects.filter(uid=uid, is_active=True)
        if user_queryset:
            user = user_queryset[0]
            order_queryset = OrderInfo.objects.filter(user=user, order_no=order_no)
            if order_queryset:
                order = order_queryset[0]
                channel_q = channelInfo.objects.filter(id=order.channel_id)
                if not channel_q:
                    resp['msg'] = '查询失败'
                    return Response(data=resp, status=400)
                resp['msg'] = '查询成功'
                resp['order_money'] = order.order_money
                resp['remark'] = order.remark
                resp['add_time'] = order.add_time.strftime(format("%Y-%m-%d %H:%M"))
                resp['pay_status'] = order.pay_status
                resp['order_no'] = order.order_no
                resp['order_id'] = order.order_id
                resp['pay_time'] = order.pay_time.strftime(format("%Y-%m-%d %H:%M"))
                resp['pay_url'] = order.pay_url
                resp['real_money'] = order.real_money
                resp['channel'] = channel_q[0].channel_name  # eval('obj.get_receive_way_display()')
                return Response(data=resp, status=200)
        return Response(data=resp, status=400)


@csrf_exempt
def device_login(request):
    resp = {'msg': '操作成功'}
    if request.method == 'POST':
        result = request.body
        try:
            dict_result = json.loads(result)
        except Exception:
            code = 400
            resp['msg'] = '请求方式错误,请用json格式传参'
            return JsonResponse(resp, status=code)
        username = dict_result.get('username')
        password = dict_result.get('password')
        device_queryset = DeviceInfo.objects.filter(device_name=username)
        if not device_queryset:
            code = 400
            resp['msg'] = '登录失败'
            return JsonResponse(resp, status=code)
        device_obj = device_queryset[0]
        if device_obj.password != password:
            code = 400
            resp['msg'] = '登录失败'
            return JsonResponse(resp, status=code)
        auth_code = device_obj.auth_code
        payload = {
            "id": device_obj.id,
            "devicename": device_obj.device_name,
            "auth_code": device_obj.auth_code,
            "exp": int(time.time()) + 86400,
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256')
        code = 200
        resp['id'] = device_obj.id
        resp['auth_code'] = auth_code
        resp['token'] = token.decode('utf8')
        return JsonResponse(resp, status=code)
    else:
        code = 400
        resp['msg'] = '仅支持POST'
        return JsonResponse(resp, status=code)


from utils import googletotp


class UserGoogleBindViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin, mixins.CreateModelMixin):
    permission_classes = (IsAuthenticated, IsUserOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    def get_queryset(self):
        user = self.request.user
        return UserProfile.objects.filter(id=user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'update':
            return GoogleOnlyUserInfoSerializer
        return GoogleOnlyUserInfoSerializer

    def get_object(self):
        return self.request.user

    def create(self, request, *args, **kwargs):
        user = self.request.user
        resp = {}
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        safe_code = serializer.validated_data.get('safe_code')
        if make_md5(safe_code) == user.safe_code:
            resp['msg'] = '谷歌验证绑定成功'
            code = 201
            base_32_secret = base64.b32encode(
                codecs.decode(codecs.encode('{0:020x}'.format(random.getrandbits(80))), 'hex_codec'))
            totp_obj = googletotp.TOTP(base_32_secret.decode("utf-8"))
            qr_code = re.sub(r'=+$', '', totp_obj.provisioning_uri(request.user.username, issuer_name="帅气的验证码"))
            key = str(base_32_secret, encoding="utf-8")
            try:
                g = Google2Auth()
                g.user = user
                g.key = key
                g.save()
                user.is_google = True
                user.save()
                resp['key'] = key
                resp['qrcode'] = qr_code
                return Response(data=resp, status=code)
            except Exception:
                resp['msg'] = '令牌已绑定'
                code = 400
                return Response(data=resp, status=code)
            # Google2Auth.objects.create(user=user)

        else:
            resp['msg'] = '操作码错误'
            code = 400
            return Response(data=resp, status=code)


@csrf_exempt
def login(request):
    resp = {'msg': '操作成功'}
    if request.method == 'POST':
        result = request.body
        try:
            dict_result = json.loads(result)
        except Exception:
            code = 400
            resp['msg'] = '请求方式错误,请用json格式传参'
            return JsonResponse(resp, status=code)
        username = dict_result.get('username')
        password = dict_result.get('password')
        user_queryset = UserProfile.objects.filter(username=username)
        if not user_queryset:
            code = 400
            resp['msg'] = '登录失败'
            return JsonResponse(resp, status=code)
        user = user_queryset[0]
        if user.check_password(password):
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            code = 200
            resp['msg'] = '登录成功'
            resp['token'] = token
            resp['level'] = user.level
            resp['username'] = user.username
            return JsonResponse(resp, status=code)
    else:
        code = 400
        resp['msg'] = '仅支持POST'
        return JsonResponse(resp, status=code)


class AlipayReceiveView(views.APIView):
    def post(self, request):
        resp = {'msg': '操作成功', 'code': 200, 'data': []}
        processed_dict = {}
        for key, value in request.data.items():
            processed_dict[key] = value
        sign = processed_dict.pop("sign", None)
        app_id = processed_dict.get('app_id', '')
        c_queryset = AlipayInfo.objects.filter(c_appid=app_id)
        if c_queryset:
            c_model = c_queryset[0]
            print('c_model', c_model)
            private_key_path = c_model.c_private_key
            ali_public_path = c_model.alipay_public_key
            alipay = AliPay(
                appid=app_id,
                app_notify_url=APP_NOTIFY_URL,
                app_private_key_path=private_key_path,
                alipay_public_key_path=ali_public_path,
                debug=ALIPAY_DEBUG,  # 默认False,
                return_url=None
            )
            try:
                # 验证通过返回True
                verify_result = alipay.verify(processed_dict, sign)
            except:
                resp['msg'] = '操作失败'
                resp['code'] = 400
                return Response(resp)
            pay_status = processed_dict.get("trade_status", "")
            print('pay_status', pay_status, verify_result)
            if verify_result is True and pay_status == "TRADE_SUCCESS":
                trade_no = processed_dict.get("trade_no", None)
                order_no = processed_dict.get("out_trade_no", None)
                print('trade_no', trade_no, 'order_no', order_no)
                total_amount = processed_dict.get("total_amount", 0)
                exited_set = OrderInfo.objects.filter(order_no=order_no)
                if not exited_set:
                    resp['msg'] = '查找失败'
                    resp['code'] = 400
                    return Response(resp)
                exited_order = exited_set[0]
                user_id = exited_order.user_id
                user_info = UserProfile.objects.filter(id=user_id)[0]
                if exited_order.pay_status == 0:
                    # exited_order.trade_no = trade_no
                    exited_order.pay_status = 1
                    exited_order.trade_no = trade_no
                    exited_order.pay_time = datetime.datetime.now()
                    exited_order.save()
                    # 处理支付宝卡 可变余额 切 关闭
                    c_model.variable_money = c_model.variable_money - exited_order.order_money
                    if c_model.variable_money <= 0:
                        c_model.is_active = False
                    c_model.save()
                    # 查找alipay通道费率
                    c_queryset = channelInfo.objects.filter(channel_name='alipay')
                    if not c_queryset:
                        resp['msg'] = '找不到对应通道'
                        code = 404
                        return Response(data=resp, status=code)
                    R_queryset = RateInfo.objects.filter(user_id=user_id, is_active=True, is_map=True,
                                                         channel_id=c_queryset[0].id)
                    if R_queryset:
                        mapid = R_queryset[0].mapid
                        new_queryset = RateInfo.objects.filter(id=mapid)
                        rate = new_queryset[0].rate
                    else:
                        RR_queryset = RateInfo.objects.filter(user_id=user_id, is_active=True,
                                                              channel_id=c_queryset[0].id)
                        if not RR_queryset and len(R_queryset) != 1:
                            resp['msg'] = '找不到对应费率'
                            code = 404
                            return Response(data=resp, status=code)
                        else:
                            rate = RR_queryset[0].rate
                    # 算费 计算后金额
                    real_money = Decimal(total_amount) - Decimal(total_amount) * Decimal(rate)
                    print('计算后金额', real_money)
                    # 更新用户收款
                    user_info.total_money = (user_info.total_money + Decimal(real_money))
                    user_info.money = (user_info.money + Decimal(real_money))
                    # 更新代理收款
                    daili_obj = UserProfile.objects.get(id=exited_order.proxy)
                    daili_obj.total_money = (daili_obj.total_money + Decimal(real_money))
                    daili_obj.money = (daili_obj.money + Decimal(real_money))
                    # 更新商家存钱
                    c_model.total_money = (c_model.total_money + Decimal(real_money))
                    c_model.last_time = datetime.datetime.now()
                    # 保存
                    c_model.save()
                    user_info.save()
                    daili_obj.save()

                '支付状态，下单时间，支付时间，商户订单号'
                notify_url = exited_order.notify_url
                if not notify_url:
                    return Response('success')
                data_dict = {}
                data_dict['pay_status'] = pay_status
                data_dict['add_time'] = str(exited_order.add_time.strftime(format("%Y-%m-%d %H:%M")))
                data_dict['pay_time'] = str(exited_order.pay_time.strftime(format("%Y-%m-%d %H:%M")))
                data_dict['total_amount'] = total_amount
                data_dict['order_id'] = exited_order.order_id
                data_dict['order_no'] = exited_order.order_no
                data_dict['remark'] = exited_order.remark
                resp['data'] = data_dict
                r = json.dumps(resp)
                headers = {'Content-Type': 'application/json'}
                try:
                    res = requests.post(notify_url, headers=headers, data=r, timeout=5, stream=True)
                    print('res.text', res.text)
                    return Response(data=res.text, status=200)
                except requests.exceptions.Timeout:
                    exited_order.pay_status = 'NOTICE_FAIL'
                    exited_order.save()
                    return Response('超时')
        resp = {'msg': '验签失败', 'code': 400, 'data': {}}
        return Response(resp)

    def get(self, request):
        return Response('仅支持POST')
