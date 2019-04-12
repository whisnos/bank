from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from channel.models import channelInfo
from proxy.models import RateInfo, DeviceInfo, ReceiveBankInfo
from trade.models import OrderInfo, WithDrawInfo
from user.models import UserProfile


class ProxyUserDetailSerializer(serializers.ModelSerializer):
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


class ProxyRateInfoCreateSerializer(serializers.ModelSerializer):
    rate = serializers.DecimalField(max_digits=4, decimal_places=3, required=True)
    channel_id = serializers.IntegerField(required=True)
    user_id = serializers.IntegerField(required=True)
    class Meta:
        model = RateInfo
        fields = ['rate', 'channel_id', 'user_id']
        validators = [
            UniqueTogetherValidator(
                queryset=RateInfo.objects.all(),
                fields=('channel_id', 'user_id')
            )
        ]


class ProxyRateInfoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateInfo
        fields = '__all__'


class UpdateRateInfoSerializer(serializers.ModelSerializer):
    rate = serializers.DecimalField(max_digits=4, decimal_places=3, required=False)
    is_map = serializers.BooleanField(required=False)
    mapid = serializers.IntegerField(required=False)

    def validate(self, attrs):
        print("attrs.get('is_map')", attrs.get('is_map'))
        if str(attrs.get('is_map')) not in ['True', 'False', 'None']:
            raise serializers.ValidationError('传值错误')
        return attrs

    class Meta:
        model = RateInfo
        fields = ['rate', 'is_map', 'mapid']


# class ProxyOrderInfoDetailSerializer(serializers.ModelSerializer):
#     add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
#     channel = serializers.SerializerMethodField()
#     device = serializers.SerializerMethodField()
#     username = serializers.SerializerMethodField()
#     rate = serializers.SerializerMethodField()
#
#     def get_rate(self, instance):
#         channelid = instance.channel_id
#         userid = instance.user_id
#         rate_queryset = RateInfo.objects.filter(channel_id=channelid, user_id=userid)
#         if rate_queryset:
#             return rate_queryset[0].rate
#         return '加载中'
#
#     def get_username(self, instance):
#         user_obj = UserProfile.objects.filter(id=instance.proxy)[0]
#         return user_obj.username
#
#     def get_device(self, instance):
#         device_obj = DeviceInfo.objects.filter(id=instance.device_id)[0]
#         return device_obj.device_name
#
#     def get_channel(self, instance):
#         channel_obj = channelInfo.objects.filter(id=instance.channel_id)[0]
#         return channel_obj.channel_name
#
#     class Meta:
#         model = OrderInfo
#         fields = '__all__'


class ProxyWithDrawInfoDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = WithDrawInfo
        fields = '__all__'


class ProxyWithDrawInfoUpdateDetailSerializer(serializers.ModelSerializer):
    remark = serializers.CharField(required=False)
    withdraw_status = serializers.IntegerField(required=False)

    class Meta:
        model = WithDrawInfo
        fields = ['withdraw_status', 'remark']


class ProxyDeviceInfoDetailSerializer(serializers.ModelSerializer):
    # remark = serializers.CharField(required=False)
    # withdraw_status = serializers.IntegerField(required=False)
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = DeviceInfo
        fields = '__all__'


class ProxyDeviceUpdateDetailSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = DeviceInfo
        fields = ['is_active']


class ProxyWithDrawInfoCreSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(label='用户名', required=True, min_length=5, max_length=20, allow_blank=False,
                                        validators=[
                                            UniqueValidator(queryset=DeviceInfo.objects.all(), message='用户名不能重复')
                                        ], help_text='用户名')
    password = serializers.CharField(label='密码', write_only=True, required=True, allow_blank=False, min_length=6,
                                     style={'input_type': 'password'}, help_text='密码')
    password2 = serializers.CharField(label='确认密码', write_only=True, required=True, allow_blank=False, min_length=6,
                                      style={'input_type': 'password'}, help_text='重复密码')
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次输入密码不一致')
        return attrs

    class Meta:
        model = DeviceInfo
        fields = ['user', 'device_name', 'password', 'password2']


class ProxyReceiveBankInfoDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = ReceiveBankInfo
        fields = '__all__'


class ProxyReceiveBankInfoRetriDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    # device = serializers.IntegerField(label='设备id')

    class Meta:
        model = ReceiveBankInfo
        fields = '__all__'


class ProxyReceiveBankInfoUpdateDetailSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    is_active = serializers.BooleanField(required=False)
    username = serializers.CharField(label='用户名', required=False, min_length=1, max_length=20, allow_blank=False,
                                     help_text='用户名')
    card_number = serializers.CharField(required=False, validators=[
        UniqueValidator(queryset=ReceiveBankInfo.objects.all(), message='卡号不能重复')
    ], label='银行卡号')
    bank_type = serializers.CharField(required=False, label='银行类型')
    bank_mark = serializers.CharField(required=False, label='银行编号')
    bank_tel = serializers.CharField(required=False, label='银行电话')
    card_index = serializers.CharField(required=False, label='卡索引')
    mobile = serializers.CharField(required=False, max_length=11, min_length=11, label='卡索引')
    device = serializers.IntegerField(required=False)

    class Meta:
        model = ReceiveBankInfo
        exclude = ('id', 'add_time', 'total_money')


class ProxyReceiveBankCreDetailSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    username = serializers.CharField(label='用户名', required=True, min_length=1, max_length=20, allow_blank=False,
                                     help_text='用户名')
    card_number = serializers.CharField(required=True, validators=[
        UniqueValidator(queryset=ReceiveBankInfo.objects.all(), message='卡号不能重复')
    ], label='银行卡号')
    bank_type = serializers.CharField(required=True, label='银行类型')
    bank_mark = serializers.CharField(required=True, label='银行编号')
    bank_tel = serializers.CharField(required=True, label='银行电话')
    card_index = serializers.CharField(required=True, label='卡索引')
    device = serializers.IntegerField(required=True, label='设备id')

    class Meta:
        model = ReceiveBankInfo
        fields = ['user', 'username', 'card_number', 'bank_type', 'bank_mark', 'bank_tel', 'card_index', 'device']
