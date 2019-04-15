import datetime
import re
import time

from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, views, serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from channel.models import channelInfo
from proxy.filters import WithDrawFilter
from proxy.views import UserListPagination
from spuser.filters import AdminProxyFilter, AdminOrderFilter, AdminChannelFilter
from spuser.models import NoticeInfo, LogInfo
from spuser.serializers import AdminUserDetailSerializer, AdminProxyCreateSerializer, AdminUpdateSerializer, \
    AdminUpdateUserSerializer, AdminChannelDetailSerializer, AdminChannelCreateSerializer, AdminOrderDetailSerializer, \
    AdminWithDrawInfoDetailSerializer, AdminNoticeInfoDetailSerializer, AdminProxyUpdateSerializer, \
    AdminCountDetailSerializer, AdminCUserDetailSerializer, ReleaseSerializer, \
    AdminCODataSerializer, AdminCODataRetrieveSerializer, AdminCDataOrderSerializer, OrderChartListSerializer
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
    permission_classes = [IsAdminUser]
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
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminOrderFilter

    def make_userlist(self):
        user_list = [users.id for users in UserProfile.objects.filter(proxy_id=self.request.user.id)]
        return user_list

    def get_queryset(self):
        user = self.request.user
        return OrderInfo.objects.all().order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        return AdminOrderDetailSerializer


class AdminWithDrawViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                           mixins.DestroyModelMixin):
    permission_classes = [IsAdminUser]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    filter_backends = (DjangoFilterBackend,)
    filter_class = WithDrawFilter

    def get_queryset(self):
        return WithDrawInfo.objects.all().order_by('-id')  # .order_by('-add_time')

    def get_serializer_class(self):
        return AdminWithDrawInfoDetailSerializer


class AdminNoticeViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                         mixins.DestroyModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin):
    permission_classes = (IsAdminUser,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    # filter_backends = (DjangoFilterBackend,)
    # filter_class = WithDrawFilter
    filter_backends = (SearchFilter,)
    search_fields = ('title', "content")

    def get_queryset(self):
        return NoticeInfo.objects.all().order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        return AdminNoticeInfoDetailSerializer

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


class PublicNoticeViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    # filter_backends = (DjangoFilterBackend,)
    # filter_class = WithDrawFilter
    filter_backends = (SearchFilter,)
    search_fields = ('title', "content")

    def get_queryset(self):
        return NoticeInfo.objects.all().order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        return AdminNoticeInfoDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]


class AdminCountViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = [IsAdminUser]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter

    def get_queryset(self):
        return UserProfile.objects.filter(level=2).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        return AdminCountDetailSerializer


class AdminCUserViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = [IsAdminUser, ]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminProxyFilter

    def get_queryset(self):
        return UserProfile.objects.filter(level=3).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        return AdminCUserDetailSerializer


class AdminDeleteViewset(mixins.DestroyModelMixin, viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAdminUser,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = ReleaseSerializer
    pagination_class = UserListPagination

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        return []

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        resp = {'msg': '操作成功'}
        processed_dict = {}
        for key, value in self.request.data.items():
            processed_dict[key] = value
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        s_time = serializer.validated_data.get('s_time', '')
        e_time = serializer.validated_data.get('e_time', '')
        dele_type = serializer.validated_data.get('dele_type', '')
        safe_code = serializer.validated_data.get('safe_code', '')
        new_key = make_md5(safe_code)
        if new_key == user.safe_code:
            if dele_type == 'order':
                order_queryset = OrderInfo.objects.filter(add_time__range=(s_time, e_time))
            elif dele_type == 'money':
                order_queryset = WithDrawInfo.objects.filter(add_time__range=(s_time, e_time))
            elif dele_type == 'log':
                order_queryset = LogInfo.objects.filter(add_time__range=(s_time, e_time))
            else:
                code = 400
                resp['msg'] = '类型错误'
                return Response(data=resp, status=code)
            if order_queryset:
                for obj in order_queryset:
                    print(obj.id)
                    obj.delete()
            code = 200
            return Response(data=resp, status=code)
        else:
            code = 400
            resp['msg'] = '操作密码错误'
            return Response(data=resp, status=code)


class AdminWDataViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAdminUser,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = AdminCDataOrderSerializer

    def list(self, request, *args, **kwargs):
        resp = {}  # ?s_time=2019-4-12&e_time=2019-4-16
        user_queryset = UserProfile.objects.filter(level=3)
        # 总金额
        total_money = user_queryset.aggregate(
            total_money=Sum('total_money')).get('total_money', '0')
        # 可提现
        ke_money = user_queryset.aggregate(
            money=Sum('money')).get('money', '0')
        # 已提现
        withd_queryset = WithDrawInfo.objects.filter(withdraw_status=1)
        yi_money = withd_queryset.aggregate(
            withdraw_money=Sum('withdraw_money')).get('withdraw_money', '0')
        # 提现中
        withd_queryset = WithDrawInfo.objects.filter(withdraw_status=0)
        zhong_money = withd_queryset.aggregate(
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


class AdminCDataViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAdminUser,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = AdminCDataOrderSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resp = {}  # ?s_time=2019-4-12&e_time=2019-4-16
        now = datetime.datetime.now()
        # 今天零点
        a_time = (now - datetime.timedelta(hours=now.hour, minutes=now.minute))
        t_time=a_time.strftime('%Y-%m-%d %H:%M')
        te_time = (a_time + datetime.timedelta(hours=23, minutes=59, seconds=59)).strftime('%Y-%m-%d %H:%M') # .strftime('%Y-%m-%d %H:%M')
        s_time = request.GET.get('start_time', t_time)
        e_time = request.GET.get('end_time', te_time)
        if not s_time or not e_time:
            s_time = t_time
            e_time = te_time
        print('t_time',t_time,te_time)
        if not re.match(r'^(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})$', str(s_time)):
            code = 400
            resp['msg'] = '时间格式错误'
            return Response(data=resp, status=code)
        if not re.match(r'^(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})$', str(e_time)):
            code = 400
            resp['msg'] = '时间格式错误'
            return Response(data=resp, status=code)
        order_queryset = OrderInfo.objects.filter(
            add_time__range=(s_time, e_time))  # Q(add_time__gte=s_time) | Q(add_time__lte=e_time)
        all_money = order_queryset.aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        success_money = order_queryset.filter(pay_status=1).aggregate(
            real_money=Sum('real_money')).get('real_money', '0')
        all_num = order_queryset.count()
        success_num = order_queryset.filter(pay_status=1).count()

        # user_queryset = UserProfile.objects.filter(level=3)
        # # 总金额
        # total_money = user_queryset.aggregate(
        #     total_money=Sum('total_money')).get('total_money', '0')
        # # 可提现
        # ke_money = user_queryset.aggregate(
        #     money=Sum('money')).get('money', '0')
        # # 已提现
        # withd_queryset = WithDrawInfo.objects.filter(withdraw_status=1)
        # yi_money = withd_queryset.aggregate(
        #     withdraw_money=Sum('withdraw_money')).get('withdraw_money', '0')
        # # 提现中
        # withd_queryset = WithDrawInfo.objects.filter(withdraw_status=0)
        # zhong_money = withd_queryset.aggregate(
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


class GetPayView(views.APIView):
    def get(self, request):
        user = request.user
        s_time = request.GET.get('s_time')
        e_time = request.GET.get('e_time')
        print(s_time, e_time)
        if user.is_superuser:
            order_queryset = OrderInfo.objects.filter(Q(add_time__lte=s_time) | Q(add_time__gte=e_time)).aggregate(
                real_money=Sum('real_money'))
            print('order_queryset', order_queryset)
            a = order_queryset.get('real_money', '0')
            print(a)
            resp = {'msg': '操作成功'}
            code = 200
            return Response(data=resp, status=code)
        else:
            resp = {'msg': '操作失败'}
            code = 400
            return Response(data=resp, status=code)


class PublicChannelViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = [IsAuthenticated]
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    filter_backends = (DjangoFilterBackend,)
    filter_class = AdminChannelFilter

    def get_queryset(self):
        return channelInfo.objects.all().order_by('-id')  # .order_by('-add_time')

    def get_serializer_class(self):
        return AdminChannelDetailSerializer


class AdminADataViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAdminUser,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    # serializer_class = CDataOrderSerializer

    def list(self, request, *args, **kwargs):
        resp = {}  # ?s_time=2019-4-12&e_time=2019-4-16
        order_queryset = OrderInfo.objects.all()  # Q(add_time__gte=s_time) | Q(add_time__lte=e_time)
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


class AdminCODataViewset(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (IsAdminUser,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    def get_queryset(self):
        return UserProfile.objects.filter(level=2).order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminCODataRetrieveSerializer
        return AdminCODataSerializer

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        resp = {}  # ?s_time=2019-4-12&e_time=2019-4-16
        # 处理时间
        now = datetime.datetime.now()
        # 今天零点
        a_time = (now - datetime.timedelta(hours=now.hour, minutes=now.minute))
        t_time = a_time.strftime('%Y-%m-%d %H:%M')
        te_time = (a_time + datetime.timedelta(hours=23, minutes=59, seconds=59)).strftime(
            '%Y-%m-%d %H:%M')  # .strftime('%Y-%m-%d %H:%M')
        s_time = request.GET.get('start_time', t_time)
        e_time = request.GET.get('end_time', te_time)
        print('e_time',s_time,e_time)
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

        order_queryset = OrderInfo.objects.filter(add_time__range=(s_time, e_time),
                                                  proxy=user.id)  # Q(add_time__gte=s_time) | Q(add_time__lte=e_time)
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


class AdminCUDataViewset(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (IsAdminUser,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination

    def get_queryset(self):
        return UserProfile.objects.filter(level=3).order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminCODataRetrieveSerializer
        return AdminCODataSerializer

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        resp = {}  # ?s_time=2019-4-12&e_time=2019-4-16
        # 处理时间
        now = datetime.datetime.now()
        # 今天零点
        a_time = (now - datetime.timedelta(hours=now.hour, minutes=now.minute))
        t_time = a_time.strftime('%Y-%m-%d %H:%M')
        te_time = (a_time + datetime.timedelta(hours=23, minutes=59, seconds=59)).strftime(
            '%Y-%m-%d %H:%M')  # .strftime('%Y-%m-%d %H:%M')
        s_time = request.GET.get('start_time', t_time)
        e_time = request.GET.get('end_time', te_time)
        print('e_time',s_time,e_time)
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

        order_queryset = OrderInfo.objects.filter(add_time__range=(s_time, e_time),
                                                  user_id=user.id)  # Q(add_time__gte=s_time) | Q(add_time__lte=e_time)
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
class AdminChartViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = OrderChartListSerializer
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    def get_queryset(self):
        return OrderInfo.objects.filter(
            Q(pay_status=1) | Q(pay_status=3),
            add_time__gte=time.strftime('%Y-%m-%d', time.localtime()),
        ).order_by('-add_time')
