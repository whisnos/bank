from django.shortcuts import render
from rest_framework import viewsets, mixins
# Create your views here.
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from proxy.views import UserListPagination
from user.models import UserProfile
from user.serializers import UserDetailSerializer, UpdateUserInfoSerializer
from utils.make_code import make_auth_code, make_md5
from utils.permissions import IsOwnerOrReadOnly


class UserInfoViewset(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = UserListPagination
    def get_queryset(self):
        user = self.request.user
        print('user.level', user.level)
        # if user.level == 3:
        # return UserDetailSerializer(user)
        return UserProfile.objects.filter(id=user.id)  # .order_by('-add_time')
        # return []

    def get_serializer_class(self):
        if self.action == 'update':
            return UpdateUserInfoSerializer
        return UserDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

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
            serializer=UserDetailSerializer(user)
            return Response(data=serializer.data, status=code)
        code = 403
        resp['msg'] = '没有操作权限'
        return Response(data=resp, status=code)
