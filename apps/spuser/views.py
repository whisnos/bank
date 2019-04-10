from django.shortcuts import render

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from channel.models import channelInfo
from proxy.filters import WithDrawFilter
from proxy.views import UserListPagination
from spuser.filters import AdminProxyFilter, AdminOrderFilter
from spuser.serializers import AdminUserDetailSerializer, AdminProxyCreateSerializer, AdminUpdateSerializer, \
    AdminUpdateUserSerializer, AdminChannelDetailSerializer, AdminChannelCreateSerializer, AdminOrderDetailSerializer, \
    AdminWithDrawInfoDetailSerializer
from trade.models import OrderInfo, WithDrawInfo
from user.models import UserProfile
from utils.make_code import make_uuid_code, make_auth_code, make_md5
from utils.permissions import IsOwnerOrReadOnly


class AdminProxyViewset(mixins.ListModelMixin, viewsets.GenericViewSet,
                        mixins.CreateModelMixin,mixins.DestroyModelMixin,mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter

    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        if user.is_superuser:
            return UserProfile.objects.filter(level=2).order_by('-add_time')  # .order_by('-add_time')
        return []

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminProxyCreateSerializer
        return AdminUserDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    # def get_object(self):
    #     return self.request.user

    def create(self, request, *args, **kwargs):
        resp = {'msg': []}
        proxy_user = self.request.user
        if proxy_user.is_superuser:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
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
                            mixins.UpdateModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter

    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        if user.is_superuser:
            return UserProfile.objects.filter(level=3).order_by('-add_time')  # .order_by('-add_time')
        return []

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminProxyCreateSerializer
        elif self.action == 'update':
            return AdminUpdateUserSerializer
        return AdminUserDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        admin_user = self.request.user
        user = self.get_object()
        resp = {'msg': []}
        if admin_user.level == 1:
            code = 204
            resp['id'] = user.id
            resp['msg'] = '删除成功'
            self.perform_destroy(user)
            return Response(data=resp, status=code)
        else:
            code = 403
            resp['msg'] = '没有操作权限'
            return Response(data=resp, status=code)

    def update(self, request, *args, **kwargs):
        admin_user = self.request.user
        user = self.get_object()
        resp = {'msg': []}
        code = 200
        if admin_user.is_superuser:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            print('self.request.data', request.data)
            password = self.request.data.get('password', '')
            password2 = self.request.data.get('password2', '')
            auth_code = self.request.data.get('auth_code', '')
            safe_code = self.request.data.get('safe_code', '')
            safe_code2 = self.request.data.get('safe_code2', '')
            is_active = serializer.validated_data.get('is_active', '')
            if password:
                if password == password2:
                    user.set_password(password)
                elif password != password2:
                    code = 400
            if auth_code:
                user.auth_code = make_auth_code()
            if safe_code == safe_code2:
                if safe_code:
                    print('admin修改 商户 操作密码中..........')
                    safe_code = make_md5(safe_code)
                    user.safe_code = safe_code
            else:
                code = 400
            if str(is_active):
                if is_active:
                    user.is_active = is_active
                if is_active == False:
                    user.is_active = is_active
            user.save()
            serializer = AdminUserDetailSerializer(user)
            return Response(data=serializer.data, status=code)
        else:
            code = 403
            resp['msg'] = '没有操作权限'
            return Response(data=resp, status=code)


class AdminChannelViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.CreateModelMixin,
                          mixins.UpdateModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    # filter_backends = (DjangoFilterBackend,)
    # filter_class = AdminProxyFilter

    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        # if user.level == 1:
        return channelInfo.objects.all().order_by('-id')  # .order_by('-add_time')
        # return []

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminChannelCreateSerializer
        return AdminChannelDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def update(self, request, *args, **kwargs):
        resp = {'msg': []}
        admin_user = self.request.user
        channel_obj = self.get_object()
        print('admin_user', admin_user)
        if admin_user.is_superuser:
            partial = kwargs.pop('partial', False)
            serializer = self.get_serializer(channel_obj, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            code = 200
            resp['msg'] = '创建成功'
            serializer = AdminChannelDetailSerializer(channel_obj)
            return Response(data=serializer.data, status=code)
        else:
            code = 403
            resp['msg'] = '没有操作权限'
            return Response(data=resp, status=code)

    def destroy(self, request, *args, **kwargs):
        admin_user = self.request.user
        user = self.get_object()
        resp = {'msg': []}
        if admin_user.is_superuser:
            code = 204
            resp['id'] = user.id
            resp['msg'] = '删除成功'
            self.perform_destroy(user)
            return Response(data=resp, status=code)
        else:
            code = 403
            resp['msg'] = '没有操作权限'
            return Response(data=resp, status=code)

    def create(self, request, *args, **kwargs):
        resp = {'msg': []}
        admin_user = self.request.user
        print('admin_user', admin_user)
        if admin_user.is_superuser:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            channel = channelInfo.objects.create(**validated_data)
            code = 200
            resp['msg'] = '创建成功'
            serializer = AdminChannelDetailSerializer(channel)
            return Response(data=serializer.data, status=code)
        else:
            code = 403
            resp['msg'] = '没有操作权限'
            return Response(data=resp, status=code)

class AdminOrderViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminOrderFilter

    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        if user.is_superuser:
            return OrderInfo.objects.all().order_by('-id')  # .order_by('-add_time')
        return []

    def get_serializer_class(self):
        # if self.action == 'create':
        #     return AdminChannelCreateSerializer
        return AdminOrderDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

class AdminWithDrawViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    filter_backends = (DjangoFilterBackend,)
    filter_class = WithDrawFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return WithDrawInfo.objects.all().order_by('-id')  # .order_by('-add_time')
        return []

    def get_serializer_class(self):
        return AdminWithDrawInfoDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]