import re

from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from proxy.models import RateInfo
from trade.models import OrderInfo, WithDrawInfo, WithDrawBankInfo
from user.models import UserProfile
from utils.make_code import make_uuid_code, make_auth_code


class UserDetailSerializer(serializers.ModelSerializer):
    # add_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M', read_only=True)
    # username = serializers.CharField(label='用户名', read_only=True, allow_blank=False, help_text='用户名')
    # uid = serializers.CharField(label='用户uid', read_only=True, allow_blank=False, help_text='用户uid')
    # mobile = serializers.CharField(label='手机号', read_only=True, allow_blank=False, help_text='手机号')
    # auth_code = serializers.CharField(label='用户授权码', read_only=True, allow_blank=False, help_text='用户授权码')
    # is_proxy = serializers.BooleanField(label='是否代理', read_only=True)
    # total_money = serializers.CharField(read_only=True)
    # proxys = ProxysSerializer(many=True, read_only=True)
    # banks = BankInfoSerializer(many=True, read_only=True)
    #
    # add_money = serializers.DecimalField(max_digits=7, decimal_places=2, help_text='加款', write_only=True,
    #                                      required=False)
    # minus_money = serializers.DecimalField(max_digits=7, decimal_places=2, help_text='扣款', write_only=True,
    #                                        required=False)
    #
    # is_active = serializers.BooleanField(label='是否激活', required=False)
    # service_rate = serializers.CharField(read_only=True)
    # proxy_name = serializers.SerializerMethodField(label='所属代理', read_only=True, help_text='所属代理')
    # level = serializers.CharField(read_only=True, required=False)
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'level', 'uid', 'auth_code', 'money', 'add_time', 'is_active', 'mobile', 'web_url',
                  'proxy_id']


class UpdateUserInfoSerializer(serializers.ModelSerializer):
    auth_code = serializers.CharField(write_only=True, required=False, )
    password2 = serializers.CharField(write_only=True, required=False, min_length=6,
                                      style={'input_type': 'password'}, )
    password = serializers.CharField(write_only=True, required=False, min_length=6,
                                     style={'input_type': 'password'}, help_text='密码')

    class Meta:
        model = UserProfile
        fields = ['auth_code', 'password', 'password2']


class ProxyUserCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(label='用户名', required=True, min_length=5, max_length=20, allow_blank=False,
                                     validators=[
                                         UniqueValidator(queryset=UserProfile.objects.all(), message='用户名不能重复')
                                     ], help_text='用户名')
    password = serializers.CharField(label='密码', write_only=True, required=True, allow_blank=False, min_length=6,
                                     style={'input_type': 'password'}, help_text='密码')
    password2 = serializers.CharField(label='确认密码', write_only=True, required=True, allow_blank=False, min_length=6,
                                      style={'input_type': 'password'}, help_text='重复密码')
    mobile = serializers.CharField(label='手机号', required=False, write_only=True, allow_blank=False, min_length=11,
                                   max_length=11,
                                   validators=[
                                       UniqueValidator(queryset=UserProfile.objects.all(), message='手机号不能重复')
                                   ], help_text='手机号')

    # uid = serializers.CharField(label='uid', read_only=True, validators=[
    #     UniqueValidator(queryset=UserProfile.objects.all(), message='uid不能重复')
    # ], help_text='用户uid')
    # auth_code = serializers.CharField(label='授权码', read_only=True, validators=[
    #     UniqueValidator(queryset=UserProfile.objects.all(), message='授权码不能重复')
    # ], help_text='用户授权码')

    class Meta:
        model = UserProfile
        fields = ['username', 'password', 'password2', 'mobile']

    def validate_mobile(self, data):
        if not re.match(r'^1([38][0-9]|4[579]|5[0-3,5-9]|6[6]|7[0135678]|9[89])\d{8}$', data):
            raise serializers.ValidationError('手机号格式错误')
        return data

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次输入密码不一致')
        return attrs

    # def create(self, validated_data):
    #     proxy_user = self.context['request'].user
    #     if proxy_user.level == 2:
    #         del validated_data['password2']
    #         user = UserProfile.objects.create(**validated_data)
    #         user.set_password(validated_data['password'])
    #         user.uid = make_uuid_code()
    #         user.auth_code = make_auth_code()
    #         user.is_active = False
    #
    #         user.proxy_id = proxy_user.id
    #         user.save()
    #         # 引入日志
    #         # content = '用户：' + str(user_up.username) + ' 创建用户_' + str(user.username)
    #         # log.add_logs('3', content, user_up.id)
    #         return user
    #     return proxy_user


class UserOrderListSerializer(serializers.ModelSerializer):
    pay_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M')
    add_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M')
    # username = serializers.SerializerMethodField(read_only=True)
    # user_id = serializers.SerializerMethodField(read_only=True)
    total_amount = serializers.FloatField(read_only=True)
    account_num = serializers.CharField(read_only=True)

    # def get_username(self, obj):
    #     user_queryset = UserProfile.objects.filter(id=obj.user_id)
    #     if user_queryset:
    #         return user_queryset[0].username
    #     return '暂无匹配'

    # def get_user_id(self, obj):
    #     return str(obj.user_id)

    class Meta:
        model = OrderInfo
        # fields = ['id', 'user_id', 'username', 'pay_status', 'total_amount', 'order_no', 'pay_time', 'add_time',
        #           'order_id', 'account_num']
        fields = '__all__'


class UserWithDrawListSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    proxy_name = serializers.SerializerMethodField()

    def get_proxy_name(self, instance):
        userid = instance.user_id
        user_queryset = UserProfile.objects.filter(id=userid)
        if user_queryset:
            proxy_obj = UserProfile.objects.filter(id=user_queryset[0].proxy_id)[0]
            return proxy_obj.username
        return '加载中'

    class Meta:
        model = WithDrawInfo
        fields = '__all__'


class UserWithDrawCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    receive_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    withdraw_status = serializers.IntegerField(read_only=True)
    withdraw_no = serializers.CharField(read_only=True)
    real_money = serializers.FloatField(read_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        user_money = user.total_money
        if not re.match(
                r'(^[1-9]([0-9]{1,4})?(\.[0-9]{1,2})?$)|(^(0){1}$)|(^[0-9]\.[0-9]([0-9])?$)',
                str(attrs['withdraw_money'])):
            raise serializers.ValidationError('金额输入异常')
        if attrs['withdraw_money'] > user_money or attrs['withdraw_money'] == 0:
            raise serializers.ValidationError('金额输入异常')

        return attrs

    class Meta:
        model = WithDrawInfo
        fields = '__all__'


class UserWithDrawBankListSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    class Meta:
        model = WithDrawBankInfo
        fields = '__all__'


class UserWithDrawBankCreateSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    username = serializers.CharField(required=True)
    card_number = serializers.CharField(required=True)
    open_bank = serializers.CharField(required=False)
    bank_name = serializers.CharField(required=True)
    mobile = serializers.CharField(required=True)

    class Meta:
        model = WithDrawBankInfo
        fields = '__all__'
