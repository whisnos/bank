from django.shortcuts import render

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from channel.models import channelInfo
from proxy.filters import WithDrawFilter
from proxy.views import UserListPagination
from spuser.filters import AdminProxyFilter, AdminOrderFilter, AdminChannelFilter
from spuser.models import NoticeInfo
from spuser.serializers import AdminUserDetailSerializer, AdminProxyCreateSerializer, AdminUpdateSerializer, \
    AdminUpdateUserSerializer, AdminChannelDetailSerializer, AdminChannelCreateSerializer, AdminOrderDetailSerializer, \
    AdminWithDrawInfoDetailSerializer, AdminNoticeInfoDetailSerializer, AdminProxyUpdateSerializer, \
    AdminCountDetailSerializer
from trade.models import OrderInfo, WithDrawInfo
from user.models import UserProfile
from utils.make_code import make_uuid_code, make_auth_code, make_md5
from utils.permissions import IsOwnerOrReadOnly


class AdminProxyViewset(mixins.ListModelMixin, viewsets.GenericViewSet,
                        mixins.CreateModelMixin, mixins.DestroyModelMixin, mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin):
    permission_classes = [IsAdminUser]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter

    def get_queryset(self):
        return UserProfile.objects.filter(level=2).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminProxyCreateSerializer
        elif self.action == 'update':
            return AdminProxyUpdateSerializer
        return AdminUserDetailSerializer

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

    def update(self, request, *args, **kwargs):
        admin_user = self.request.user
        user = self.get_object()
        resp = {'msg': []}
        code = 200
        if admin_user.is_superuser:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            password = self.request.data.get('password', '')
            password2 = self.request.data.get('password2', '')
            safe_code = self.request.data.get('safe_code', '')
            safe_code2 = self.request.data.get('safe_code2', '')
            if password:
                if password == password2:
                    user.set_password(password)
                elif password != password2:
                    code = 400
            if safe_code == safe_code2:
                if safe_code:
                    print('admin修改 代理 操作密码中..........')
                    safe_code = make_md5(safe_code)
                    user.safe_code = safe_code
            else:
                code = 400
            user.save()
            serializer = AdminUserDetailSerializer(user)
            return Response(data=serializer.data, status=code)
        else:
            code = 403
            resp['msg'] = '没有操作权限'
            return Response(data=resp, status=code)

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
    permission_classes = [IsAdminUser]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter

    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        return UserProfile.objects.filter(level=3).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminProxyCreateSerializer
        elif self.action == 'update':
            return AdminUpdateUserSerializer
        return AdminUserDetailSerializer

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
    permission_classes = [IsAuthenticated]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminChannelFilter

    def get_queryset(self):
        return channelInfo.objects.all().order_by('-id')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminChannelCreateSerializer
        return AdminChannelDetailSerializer

    def update(self, request, *args, **kwargs):
        resp = {'msg': []}
        channel_obj = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(channel_obj, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        code = 200
        resp['msg'] = '创建成功'
        serializer = AdminChannelDetailSerializer(channel_obj)
        return Response(data=serializer.data, status=code)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        resp = {'msg': []}
        code = 204
        resp['id'] = user.id
        resp['msg'] = '删除成功'
        self.perform_destroy(user)
        return Response(data=resp, status=code)

    def create(self, request, *args, **kwargs):
        resp = {'msg': []}
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        channel = channelInfo.objects.create(**validated_data)
        code = 200
        resp['msg'] = '创建成功'
        serializer = AdminChannelDetailSerializer(channel)
        return Response(data=serializer.data, status=code)


class AdminOrderViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin):
    permission_classes = [IsAdminUser]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    # queryset = OrderInfo.objects.all().order_by('-add_time')
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminOrderFilter

    def make_userlist(self):
        user_list = [users.id for users in UserProfile.objects.filter(proxy_id=self.request.user.id)]
        return user_list

    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        # if user.is_superuser:
        return OrderInfo.objects.all().order_by('-add_time')  # .order_by('-add_time')
        # user_list = self.make_userlist()
        # return OrderInfo.objects.filter(user_id__in=user_list).order_by('-add_time')

    def get_serializer_class(self):
        # if self.action == 'create':
        #     return AdminChannelCreateSerializer
        return AdminOrderDetailSerializer


class AdminWithDrawViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                           mixins.DestroyModelMixin):
    permission_classes = [IsAdminUser]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    filter_backends = (DjangoFilterBackend,)
    filter_class = WithDrawFilter

    # def make_userlist(self):
    #     user_list = [users.id for users in UserProfile.objects.filter(proxy_id=self.request.user.id)]
    #     return user_list

    def get_queryset(self):
        return WithDrawInfo.objects.all().order_by('-id')  # .order_by('-add_time')

    def get_serializer_class(self):
        return AdminWithDrawInfoDetailSerializer


class AdminNoticeViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                         mixins.DestroyModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    # filter_backends = (DjangoFilterBackend,)
    # filter_class = WithDrawFilter
    filter_backends = (SearchFilter,)
    search_fields = ('title', "content")

    def get_queryset(self):
        user = self.request.user
        # if user.is_superuser:
        return NoticeInfo.objects.all().order_by('-add_time')  # .order_by('-add_time')
        # return []

    def get_serializer_class(self):
        return AdminNoticeInfoDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        if self.request.user.is_superuser:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            code = 201
            self.perform_create(serializer)
            response_data = {'msg': '创建成功'}
            headers = self.get_success_headers(response_data)
            return Response(response_data, status=code, headers=headers)

        code = 403
        response_data = {'msg': '没有权限'}
        headers = self.get_success_headers(response_data)
        return Response(response_data, status=code, headers=headers)

    def update(self, request, *args, **kwargs):
        if self.request.user.is_superuser:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            code = 201
            response_data = {'msg': '修改成功'}
            headers = self.get_success_headers(response_data)
            return Response(response_data, status=code, headers=headers)

        code = 403
        response_data = {'msg': '没有权限'}
        headers = self.get_success_headers(response_data)
        return Response(response_data, status=code, headers=headers)

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

class AdminCountViewset(mixins.ListModelMixin, viewsets.GenericViewSet,mixins.RetrieveModelMixin):
    permission_classes = [IsAdminUser]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter

    def get_queryset(self):
        return UserProfile.objects.filter(level=2).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        return AdminCountDetailSerializer