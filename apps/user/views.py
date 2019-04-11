from decimal import Decimal

from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
# Create your views here.
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from proxy.filters import OrdersFilter, WithDrawFilter, WithDrawBankFilter
from proxy.views import UserListPagination
from trade.models import OrderInfo, WithDrawInfo, WithDrawBankInfo
from user.models import UserProfile
from user.serializers import UserDetailSerializer, UpdateUserInfoSerializer, UserOrderListSerializer, \
    UserWithDrawListSerializer, UserWithDrawCreateSerializer, UserWithDrawBankListSerializer, \
    UserWithDrawBankCreateSerializer
from utils.make_code import make_auth_code, make_md5, generate_order_no
from utils.permissions import IsOwnerOrReadOnly, IsUserOnly


class UserInfoViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly, IsUserOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        # if user.level == 3:
        # return UserDetailSerializer(user)
        return UserProfile.objects.filter(id=user.id).order_by('-add_time')  # .order_by('-add_time')
        # return []

    def get_serializer_class(self):
        if self.action == 'update':
            return UpdateUserInfoSerializer
        return UserDetailSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        resp = {'msg': []}
        user = self.request.user
        code = 201
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = self.request.data.get('password')
        password2 = self.request.data.get('password2')
        auth_code = self.request.data.get('auth_code')
        original_safe_code = self.request.data.get('original_safe_code')
        safe_code = self.request.data.get('safe_code')
        safe_code2 = self.request.data.get('safe_code2')
        # tuoxie001 修改自己
        if user.level == 3:
            if password:
                if password == password2:
                    user.set_password(password)
                    resp['msg'].append('密码修改成功')
                elif password != password2:
                    code = 400
                    resp['msg'].append('输入密码不一致')
            if auth_code:
                user.auth_code = make_auth_code()
                resp['msg'].append(user.auth_code)

            if original_safe_code:
                if make_md5(original_safe_code) == user.safe_code:
                    if safe_code == safe_code2:
                        if safe_code:
                            print('tuoxie001修改操作密码中..........')
                            safe_code = make_md5(safe_code)
                            self.request.user.safe_code = safe_code

                            resp['msg'].append('操作密码修改成功')
                    else:
                        code = 400
                        resp['msg'].append('操作密码输入不一致')

                else:
                    code = 400
                    resp['msg'].append('操作密码错误')

            user.save()
            serializer = UserDetailSerializer(user)
            return Response(data=serializer.data, status=code)
        code = 403
        resp['msg'] = '没有操作权限'
        return Response(data=resp, status=code)


class UserOrderViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly, IsUserOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = OrdersFilter

    # def make_userlist(self):
    #     user_list = [users.id for users in UserProfile.objects.filter(proxy_id=self.request.user.id)]
    #     return user_list
    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        # if user.level == 3:
        # return UserDetailSerializer(user)
        return OrderInfo.objects.filter(user_id=user.id).order_by('-add_time')  # .order_by('-add_time')
        # user_list = self.make_userlist()
        # return OrderInfo.objects.filter(user_id__in=user_list).order_by('-add_time')

        # return []

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
        if proxy_user.level == 3:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            withdraw_no = generate_order_no(proxy_user.id)
            validated_data['withdraw_no'] = withdraw_no
            withdraw_obj = False
            bank = validated_data.get('bank')
            with_banklist = [wd.id for wd in WithDrawBankInfo.objects.filter(user_id=proxy_user.id)]
            if bank.id in with_banklist:
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
                    withdraw_obj = WithDrawInfo.objects.create(**validated_data)
                else:
                    code = 400
                    resp['msg'] = '创建失败'
                    return Response(data=resp, status=code)
                code = 200
                resp['msg'] = '创建成功'
                serializer = UserWithDrawListSerializer(withdraw_obj)
                return Response(data=serializer.data, status=code)
            else:
                code = 400
                resp['msg'] = '绑定的银行卡id不存在'
                return Response(data=resp, status=code)
        else:
            code = 403
            resp['msg'] = '没有操作权限'
            return Response(data=resp, status=code)


class UserWithDrawBankViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                              mixins.CreateModelMixin,mixins.UpdateModelMixin,mixins.DestroyModelMixin):
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
