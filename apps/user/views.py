from decimal import Decimal

from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
# Create your views here.
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from proxy.filters import WithDrawFilter, WithDrawBankFilter
from proxy.views import UserListPagination
from spuser.filters import AdminOrderFilter, AdminProxyFilter
from spuser.serializers import AdminCountDetailSerializer
from trade.models import OrderInfo, WithDrawInfo, WithDrawBankInfo
from user.models import UserProfile
from user.serializers import UserDetailSerializer, UpdateUserInfoSerializer, UserOrderListSerializer, \
    UserWithDrawListSerializer, UserWithDrawCreateSerializer, UserWithDrawBankListSerializer, \
    UserWithDrawBankCreateSerializer, UpdateOnlyUserInfoSerializer
from utils.make_code import make_auth_code, make_md5, generate_order_no
from utils.permissions import IsOwnerOrReadOnly, IsUserOnly


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
        # auth_code = self.request.data.get('auth_code')
        auth_code =serializer.validated_data.get('auth_code')
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
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly, IsUserOnly)
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
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly, IsUserOnly)
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
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly, IsUserOnly)
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
    permission_classes = [IsUserOnly]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter

    def get_queryset(self):
        return UserProfile.objects.filter(id=self.request.user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        return AdminCountDetailSerializer
