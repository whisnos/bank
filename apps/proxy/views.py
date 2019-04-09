from decimal import Decimal

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from proxy.filters import ProxyUserFilter
from proxy.models import RateInfo
from proxy.serializers import ProxyUserDetailSerializer, ProxyRateInfoCreateSerializer, ProxyRateInfoDetailSerializer, \
    UpdateRateInfoSerializer
from user.models import UserProfile
from user.serializers import UpdateUserInfoSerializer, ProxyUserCreateSerializer

from utils.make_code import make_auth_code, make_md5, make_uuid_code
from utils.permissions import IsOwnerOrReadOnly


class UserListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    page_query_param = 'page'
    max_page_size = 100


class ProxyUserInfoViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                           mixins.CreateModelMixin,
                           mixins.UpdateModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = ProxyUserFilter

    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        return UserProfile.objects.filter(proxy_id=user.id).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'update':
            return UpdateUserInfoSerializer
        elif self.action == 'create':
            return ProxyUserCreateSerializer
        return ProxyUserDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_object(self):
        return self.request.user

    def create(self, request, *args, **kwargs):
        resp = {'msg': []}
        proxy_user = self.request.user
        if proxy_user.level == 2:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data=serializer.validated_data
            del validated_data['password2']
            user = UserProfile.objects.create(**validated_data)
            user.set_password(validated_data['password'])
            user.uid = make_uuid_code()
            user.auth_code = make_auth_code()
            user.is_active = False
            user.proxy_id = proxy_user.id
            user.save()
            code = 200
            resp['msg'] = '创建成功'
            serializer = ProxyUserDetailSerializer(user)
            return Response(data=serializer.data, status=code)
        else:
            code = 403
            resp['msg'] = '没有操作权限'
            return Response(data=resp, status=code)

    def update(self, request, *args, **kwargs):
        resp = {'msg': []}
        proxy_user = self.request.user
        code = 201
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        add_money = self.request.data.get('add_money')
        desc_money = self.request.data.get('desc_money')
        get_proxyid = self.request.data.get('id')
        web_url = self.request.data.get('web_url')
        # 代理 修改 商户
        if proxy_user.level == 2:
            if get_proxyid:
                id_list = [user_obj.id for user_obj in UserProfile.objects.filter(proxy_id=proxy_user.id)]
                if int(get_proxyid) in id_list:
                    user = UserProfile.objects.filter(id=get_proxyid)[0]
                    if add_money:
                        user.total_money = '%.2f' % (Decimal(user.total_money) + Decimal(add_money))
                        user.money = '%.2f' % (Decimal(user.money) + Decimal(add_money))
                        resp['msg'].append('加款成功')
                        # # 加日志
                        # if not ramark_info:
                        #     ramark_info = '无备注！'
                        # content = '用户：' + str(self.request.user.username) + ' 对 ' + str(
                        #     user.username) + ' 加款 ' + ' 金额 ' + str(add_money) + ' 元。' + ' 备注：' + str(ramark_info)
                        # log.add_logs('3', content, self.request.user.id)
                        # 更新代理余额
                        proxy_user.total_money = '%.2f' % (Decimal(proxy_user.total_money) + Decimal(add_money))
                        proxy_user.money = '%.2f' % (Decimal(proxy_user.money) + Decimal(add_money))
                        proxy_user.save()
                    if desc_money:
                        if Decimal(desc_money) <= Decimal(user.total_money) and Decimal(
                                proxy_user.total_money) >= Decimal(desc_money):
                            user.total_money = '%.2f' % (Decimal(user.total_money) - Decimal(desc_money))
                            user.money = '%.2f' % (Decimal(user.money) - Decimal(desc_money))
                            resp['msg'].append('扣款成功')
                            # # 加日志
                            # if not ramark_info:
                            #     ramark_info = '无备注！'
                            # content = '用户：' + str(self.request.user.username) + ' 对 ' + str(
                            #     user.username) + ' 扣款 ' + ' 金额 ' + str(minus_money) + ' 元。' + ' 备注：' + str(ramark_info)
                            # log.add_logs('3', content, self.request.user.id)
                            # 更新代理余额
                            proxy_user.total_money = '%.2f' % (Decimal(proxy_user.total_money) - Decimal(desc_money))
                            proxy_user.money = '%.2f' % (Decimal(proxy_user.money) - Decimal(desc_money))
                            proxy_user.save()
                        else:
                            code = 404
                            resp['msg'].append('余额不足，扣款失败')
                    if web_url:
                        user.web_url = web_url
                    user.save()
                    serializer=ProxyUserDetailSerializer(user)
                    return Response(data=serializer.data, status=code)
                else:
                    code = 400
                    resp['msg'].append('商户id参数错误')
                    return Response(resp, status=code)

        code = 403
        resp['msg'] = '没有操作权限'
        return Response(data=resp, status=code)


class ProxyRateInfoViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                           mixins.CreateModelMixin,
                           mixins.UpdateModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    # filter_backends = (DjangoFilterBackend,)
    # filter_class = ProxyUserFilter
    def make_userlist(self):
        user_list = [users.id for users in UserProfile.objects.filter(proxy_id=self.request.user.id)]
        return user_list
    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        user_list = self.make_userlist()
        return RateInfo.objects.filter(user_id__in=user_list).order_by('-add_time')  # .order_by('-add_time')

    def get_serializer_class(self):
        if self.action == 'update':
            return UpdateRateInfoSerializer
        elif self.action == 'create':
            return ProxyRateInfoCreateSerializer
        return ProxyRateInfoDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    # def get_object(self):
    #     return self.request.user

    def create(self, request, *args, **kwargs):
        resp = {'msg': []}
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proxy_user = self.request.user
        userid=request.data.get('user_id','')
        user_list = self.make_userlist()
        if proxy_user.level == 2:
            if userid:
                if int(userid) in user_list:
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    validated_data=serializer.validated_data
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
        else:
            code = 403
            resp['msg'] = '没有操作权限'
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
        print('is_map',is_map)
        # 代理 修改 商户
        if proxy_user.level == 2:
            if rate:
                rate_obj.rate= rate
                rate_obj.save()
            if str(is_map):
                print(6)
                if str(is_map) in ['true','True','1']:
                    print(5)
                    if is_map == '0':
                        is_map = False
                    else:
                        is_map = True
                    if mapid:
                        print(111111)
                        rate_obj.is_map = is_map
                        rate_obj.mapid = mapid
                    else:
                        code = 400
                        resp['msg'] = '映射ip必传'
                        return Response(data=resp, status=code)
                print('rate_obj1', str(is_map))
                if str(is_map) in ['false','False']:
                    print(2222)
                    is_map = False
                    rate_obj.is_map = is_map
            print('rate_obj', is_map)
            rate_obj.save()
            print('rate_obj',rate_obj.rate)
            serializer=ProxyRateInfoDetailSerializer(rate_obj)
            return Response(data=serializer.data, status=code)
        code = 403
        resp['msg'] = '没有操作权限'
        return Response(data=resp, status=code)