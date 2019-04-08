from django.shortcuts import render

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from proxy.views import UserListPagination
from spuser.filters import AdminProxyFilter
from spuser.serializers import AdminUserDetailSerializer, AdminProxyCreateSerializer, AdminUpdateSerializer
from user.models import UserProfile
from utils.make_code import make_uuid_code, make_auth_code
from utils.permissions import IsOwnerOrReadOnly


class AdminProxyViewset(mixins.ListModelMixin, viewsets.GenericViewSet,
                      mixins.CreateModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter
    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        if user.level == 1:
            return UserProfile.objects.filter(level=2).order_by('-add_time')  # .order_by('-add_time')
        return []

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminProxyCreateSerializer
        return AdminUserDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_object(self):
        return self.request.user

    def create(self, request, *args, **kwargs):
        resp = {'msg': []}
        proxy_user = self.request.user
        if proxy_user.level == 1:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data=serializer.validated_data
            del validated_data['password2']
            user = UserProfile.objects.create(**validated_data)
            user.set_password(validated_data['password'])
            user.uid = make_uuid_code()
            user.auth_code = make_auth_code()
            user.level = 2
            user.save()
            code = 200
            resp['msg'] = '创建成功'
            serializer = AdminUserDetailSerializer(user)
            return Response(data=serializer.data, status=code)
        else:
            code = 403
            resp['msg'] = '没有操作权限'
            return Response(data=resp, status=code)

class AdminuserProxyViewset(mixins.ListModelMixin, viewsets.GenericViewSet,
                      mixins.UpdateModelMixin,mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter
    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        if user.level == 1:
            return UserProfile.objects.filter(level=3).order_by('-add_time')  # .order_by('-add_time')
        return []

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminProxyCreateSerializer
        elif self.action == 'retriew':
            return AdminUpdateSerializer
        return AdminUserDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def update(self, request, *args, **kwargs):
        print('111111',self.get_object())
    # def get_object(self):
    #     return self.request.user

    # def create(self, request, *args, **kwargs):
    #     resp = {'msg': []}
    #     proxy_user = self.request.user
    #     if proxy_user.level == 1:
    #         serializer = self.get_serializer(data=request.data)
    #         serializer.is_valid(raise_exception=True)
    #         validated_data=serializer.validated_data
    #         del validated_data['password2']
    #         user = UserProfile.objects.create(**validated_data)
    #         user.set_password(validated_data['password'])
    #         user.uid = make_uuid_code()
    #         user.auth_code = make_auth_code()
    #         user.level = 2
    #         user.save()
    #         code = 200
    #         resp['msg'] = '创建成功'
    #         serializer = AdminUserDetailSerializer(user)
    #         return Response(data=serializer.data, status=code)
    #     else:
    #         code = 403
    #         resp['msg'] = '没有操作权限'
    #         return Response(data=resp, status=code)