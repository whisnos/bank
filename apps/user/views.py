import datetime
import random
import re
import time
from decimal import Decimal

from django.db.models import Sum, Q
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, views
# Create your views here.
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bank.settings import CLOSE_TIME, FONT_DOMAIN
from proxy.filters import WithDrawFilter, WithDrawBankFilter
from proxy.models import ReceiveBankInfo, DeviceInfo
from proxy.views import UserListPagination
from spuser.filters import AdminOrderFilter, AdminProxyFilter
from spuser.serializers import OrderChartListSerializer
from trade.models import OrderInfo, WithDrawInfo, WithDrawBankInfo
from user.models import UserProfile
from user.serializers import UserDetailSerializer, UserOrderListSerializer, \
    UserWithDrawListSerializer, UserWithDrawCreateSerializer, UserWithDrawBankListSerializer, \
    UserWithDrawBankCreateSerializer, UpdateOnlyUserInfoSerializer, UserCountDetailSerializer, \
    UserCODataSerializer
from utils.make_code import make_auth_code, make_md5, generate_order_no, make_short_code
from utils.pay import MakePay
from utils.permissions import IsUserOnly


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

    def get_queryset(self):
        user = self.request.user
        return OrderInfo.objects.filter(user_id=user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        # if self.action == 'update':
        #     return UpdateUserInfoSerializer
        return UserOrderListSerializer


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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        print('validated_data', validated_data)
        withdraw_no = generate_order_no(proxy_user.id)
        validated_data['withdraw_no'] = withdraw_no
        bankid = validated_data.get('bank')
        with_banklist = [wd.id for wd in WithDrawBankInfo.objects.filter(user_id=proxy_user.id)]
        if bankid in with_banklist:
            # 更新商户余额
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
                bank_queryset = WithDrawBankInfo.objects.filter(id=bankid)
                if bank_queryset:
                    bank_obj = bank_queryset[0]
                    validated_data['bank'] = bank_obj
                    withdraw_obj = WithDrawInfo.objects.create(**validated_data)
                    code = 200
                    resp['msg'] = '创建成功'
                    serializer = UserWithDrawListSerializer(withdraw_obj)
                    return Response(data=serializer.data, status=code)
                else:
                    code = 400
                    resp['msg'] = '创建失败'
                    return Response(data=resp, status=code)
            else:
                code = 400
                resp['msg'] = '创建失败'
                return Response(data=resp, status=code)
        else:
            code = 400
            resp['msg'] = '绑定的银行卡id不存在'
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
            total_money=Sum('total_money')).get('total_money', '0')
        # 可提现
        ke_money = user_queryset.aggregate(
            money=Sum('money')).get('money', '0')
        # 已提现
        withd_queryset = WithDrawInfo.objects.filter(id=self.request.user.id)
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
            real_money=Sum('real_money')).get('real_money', '0')
        success_money = order_queryset.filter(pay_status=1).aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        all_num = order_queryset.count()
        success_num = order_queryset.filter(pay_status=1).count()

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
            real_money=Sum('real_money')).get('real_money', '0')
        success_money = order_queryset.filter(pay_status=1).aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        all_num = order_queryset.count()
        success_num = order_queryset.filter(pay_status=1).count()

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
        channel = processed_dict.get('channel', '')
        # make_pay=MakePay(uid=uid,real_money=real_money,order_id=order_id,return_url=return_url,channel=channel,key=key,user_queryset=user_queryset)
        if not str(real_money) > '1':
            resp['msg'] = '金额必须大于1'
            return Response(resp, status=404)
        if not order_id:
            resp['msg'] = '请填写订单号~~'
            return Response(resp, status=404)
        if not return_url:
            resp['msg'] = '请填写正确跳转url~~'
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
        # 加密 uid + auth_code + real_money + return_url + order_id
        auth_code = user.auth_code
        new_temp = str(str(uid) + str(auth_code) + str(real_money) + str(return_url) + str(order_id))
        my_key = make_md5(new_temp)
        if key == key:

            bank_queryet = ReceiveBankInfo.objects.filter(is_active=True, user_id=user.proxy_id)
            if not bank_queryet:
                resp['code'] = 404
                resp['msg'] = '收款商户未激活,或不存在有效收款卡'
                return Response(resp)

            # 关闭超时订单
            now_time = datetime.datetime.now() - datetime.timedelta(minutes=CLOSE_TIME)
            order_queryset = OrderInfo.objects.filter(pay_status=0, add_time__lte=now_time).update(
                pay_status=2)

            device_queryset=DeviceInfo.objects.filter(user_id=user.proxy_id,is_active=True)
            if not device_queryset:
                resp['code'] = 404
                resp['msg'] = '设备未激活,或不存在有效设备'
                return Response(resp)
            decive_obj=random.choice(device_queryset)
            if channel == 'atb':
                short_code = make_short_code(8)
                order_no = "{time_str}{userid}{randstr}".format(time_str=time.strftime("%Y%m%d%H%M%S"),
                                                                userid=user.id, randstr=short_code)
                # # 处理金额
                while True:
                    for bank in bank_queryet:
                        order_queryset = OrderInfo.objects.filter(pay_status=0, order_money=order_money,account_num=bank.card_number)
                        if not order_queryset:
                            account_num = bank.card_number
                            # bank_tel = bank.bank_tel
                            break
                        else:
                            continue
                    if order_queryset:
                        order_money = (Decimal(real_money) + Decimal(random.uniform(-0.9, 0.9))).quantize(
                            Decimal('0.00'))
                    else:
                        break
                print('order_money', order_money)
                order = OrderInfo()
                order.user_id = user.id
                order.channel_id = 1
                order.device_id = decive_obj.id
                order.proxy=user.proxy_id
                order.order_no = order_no
                order.pay_status = 0
                order.order_money = order_money
                order.real_money = real_money
                order.remark = remark
                order.order_id = order_id
                order.account_num = account_num
                pay_url = FONT_DOMAIN + '/pay/' + order_no
                order.pay_url = pay_url
                # order.receive_way = '0'
                order.save()
                resp['order_no'] = order_no
                resp['pay_url'] = pay_url
                resp['id'] = order.id
            elif channel == 'wang':
                order = OrderInfo()
                order.user_id = user.id
                order.channel_id = 2
                order.device_id = decive_obj.id
                # order.order_no = order_no
                order.pay_status = 0
                order.real_money = real_money
                order.order_money = order_money
                order.remark = remark
                order.order_id = order_id
                # order.bank_tel = bank_tel
                # order.account_num = account_num
                # order.real_money = money
                order.receive_way = '0'
                order.save()
            else:
                resp['code'] = 404
                resp['msg'] = '通道不存在'
                return Response(resp)

            # 引入日志
            # log = MakeLogs()
            # content = '用户：' + str(user.username) + ' 创建订单_ ' + str(order_no) + '  金额 ' + str(total_amount) + ' 元'
            # log.add_logs('1', content, user.id)
            resp['msg'] = '创建成功'
            resp['code'] = 200
            resp['order_money'] = order_money
            resp['real_money'] = real_money
            resp['order_id'] = order_id
            resp['add_time'] = str(order.add_time)
            resp['channel'] = channel
            return Response(resp)
        resp['code'] = 404
        resp['msg'] = 'key匹配错误'
        return Response(resp)


class UserCODataViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAuthenticated,IsUserOnly)
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
        order_queryset = OrderInfo.objects.filter(add_time__range=(s_time, e_time),user_id=self.request.user.id)  # Q(add_time__gte=s_time) | Q(add_time__lte=e_time)
        all_money = order_queryset.aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        success_money = order_queryset.filter(pay_status=1).aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        all_num = order_queryset.count()
        success_num = order_queryset.filter(pay_status=1).count()

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
            add_time__gte=time.strftime('%Y-%m-%d', time.localtime()),user_id=self.request.user.id
        ).order_by('-add_time')