import re

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from channel.models import channelInfo
from trade.models import OrderInfo, WithDrawInfo
from user.models import UserProfile
from utils.make_code import make_uuid_code, make_auth_code


class AdminUserDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'level', 'uid', 'auth_code', 'money', 'add_time', 'is_active', 'mobile', 'web_url',
                  'proxy_id']


class AdminProxyCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(label='用户名', required=True, min_length=5, max_length=20, allow_blank=False,
                                     validators=[
                                         UniqueValidator(queryset=UserProfile.objects.all(), message='用户名不能重复')
                                     ], help_text='用户名')
    password = serializers.CharField(label='密码', write_only=True, required=True, allow_blank=False, min_length=6,
                                     style={'input_type': 'password'}, help_text='密码')
    password2 = serializers.CharField(label='确认密码', write_only=True, required=True, allow_blank=False, min_length=6,
                                      style={'input_type': 'password'}, help_text='重复密码')
    mobile = serializers.CharField(label='手机号', required=False, write_only=True, allow_blank=True, min_length=11,
                                   max_length=11,
                                   validators=[
                                       UniqueValidator(queryset=UserProfile.objects.all(), message='手机号不能重复')
                                   ], help_text='手机号')

    class Meta:
        model = UserProfile
        fields = ['username', 'password', 'password2', 'mobile']

    def validate_mobile(self, data):
        if data:
            if not re.match(r'^1([38][0-9]|4[579]|5[0-3,5-9]|6[6]|7[0135678]|9[89])\d{8}$', data):
                raise serializers.ValidationError('手机号格式错误')
        return data

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次输入密码不一致')
        return attrs


class AdminUpdateSerializer(serializers.ModelSerializer):
    auth_code = serializers.CharField(write_only=True, required=False, )
    password2 = serializers.CharField(write_only=True, required=False, min_length=6,
                                      style={'input_type': 'password'}, )
    password = serializers.CharField(write_only=True, required=False, min_length=6,
                                     style={'input_type': 'password'}, help_text='密码')

    class Meta:
        model = UserProfile
        fields = ['auth_code', 'password', 'password2']


class AdminUpdateUserSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(label='是否激活', required=False)
    auth_code = serializers.CharField(write_only=True, required=False)
    password2 = serializers.CharField(write_only=True, required=False, min_length=6,
                                      style={'input_type': 'password'}, )
    password = serializers.CharField(write_only=True, required=False, min_length=6,
                                     style={'input_type': 'password'}, help_text='密码')

    def validate(self, attrs):
        print("attrs.get('is_active')", attrs.get('is_active'))
        if str(attrs.get('is_active')) not in ['True', 'False', 'None']:
            raise serializers.ValidationError('传值错误')
        return attrs

    class Meta:
        model = UserProfile
        fields = ['is_active', 'auth_code', 'password', 'password2']
        # fields = '__all__'


class AdminChannelDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = channelInfo
        fields = '__all__'


class AdminChannelCreateSerializer(serializers.ModelSerializer):
    channel_name = serializers.CharField(write_only=True, validators=[
        UniqueValidator(queryset=channelInfo.objects.all(), message='通道名称不能重复')])

    class Meta:
        model = channelInfo
        fields = '__all__'


class AdminOrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = '__all__'


class AdminWithDrawInfoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithDrawInfo
        fields = '__all__'
