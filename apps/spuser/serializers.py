import datetime
import re
import time

from django.db.models import Q, Sum
from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from channel.models import channelInfo
from proxy.models import DeviceInfo, RateInfo
from spuser.models import NoticeInfo, LogInfo
from trade.models import OrderInfo, WithDrawInfo, WithDrawBankInfo
from user.models import UserProfile
from user.serializers import UserWithDrawBankListSerializer


class AdminUserDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    user_num = serializers.SerializerMethodField()

    def get_user_num(self, instance):
        number = UserProfile.objects.filter(proxy_id=instance.id).count()
        return number

    device_num_on = serializers.SerializerMethodField()

    def get_device_num_on(self, instance):
        number = DeviceInfo.objects.filter(user_id=instance.id, is_active=True).count()
        return number

    device_num_all = serializers.SerializerMethodField()

    def get_device_num_all(self, instance):
        number = DeviceInfo.objects.filter(user_id=instance.id).count()
        return number

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'level', 'uid', 'auth_code', 'money', 'add_time', 'is_active', 'mobile', 'web_url',
                  'proxy_id', 'user_num', 'device_num_on', 'device_num_all']


class AdminCODataSerializer(serializers.ModelSerializer):
    # add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    # username = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username']


class AdminCODataRetrieveSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = UserProfile
        fields = ['add_time']


class AdminProxyUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(label='密码', required=False, allow_blank=False, min_length=6,
                                     style={'input_type': 'password'}, help_text='密码')
    password2 = serializers.CharField(label='密码', required=False, allow_blank=False, write_only=True, min_length=6,
                                      style={'input_type': 'password'}, help_text='密码')
    # safe_code = serializers.CharField(label='操作密码', required=False, allow_blank=False, write_only=True, min_length=6,
    #                                   style={'input_type': 'password'}, help_text='密码')
    # safe_code2 = serializers.CharField(label='操作密码', required=False, allow_blank=False, write_only=True, min_length=6,
    #                                    style={'input_type': 'password'}, help_text='密码')
    # , 'safe_code', 'safe_code2'
    class Meta:
        model = UserProfile
        fields = ['password', 'password2']


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
    add_money = serializers.DecimalField(max_digits=7, decimal_places=2, help_text='加款', write_only=True,
                                         required=False)
    desc_money = serializers.DecimalField(max_digits=7, decimal_places=2, help_text='扣款', write_only=True,
                                          required=False)
    remark = serializers.CharField(write_only=True, required=False)
    def validate_add_money(self, data):
        print(data)
        if not re.match(r"(^[1-9]([0-9]{1,4})?(\.[0-9]{1,2})?$)|(^(0){1}$)|(^[0-9]\.[0-9]([0-9])?$)", str(data)):
            raise serializers.ValidationError('请输入正确的金额')
        return data
    def validate_desc_money(self, data):
        print(data)
        if not re.match(r"(^[1-9]([0-9]{1,4})?(\.[0-9]{1,2})?$)|(^(0){1}$)|(^[0-9]\.[0-9]([0-9])?$)",str(data)):
            raise serializers.ValidationError('请输入正确的金额')
        return data
    def validate(self, attrs):
        if str(attrs.get('is_active')) not in ['True', 'False', 'None']:
            raise serializers.ValidationError('传值错误')
        return attrs

    class Meta:
        model = UserProfile
        fields = ['is_active', 'auth_code', 'password', 'password2', 'add_money', 'desc_money', 'remark']
        # fields = '__all__'


class AdminChannelDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    class Meta:
        model = channelInfo
        fields = '__all__'


class AdminChannelCreateSerializer(serializers.ModelSerializer):
    channel_name = serializers.CharField(write_only=True, validators=[
        UniqueValidator(queryset=channelInfo.objects.all(), message='通道名称不能重复')])
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = channelInfo
        fields = '__all__'


class AdminOrderDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    pay_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    channel = serializers.SerializerMethodField()
    device = serializers.SerializerMethodField()
    user = serializers.CharField(read_only=True, )
    # pay_status = serializers.SerializerMethodField()
    #
    # def get_pay_status(self, instance):
    #     return eval('instance.get_pay_status_display()')
    rate = serializers.SerializerMethodField()

    def get_rate(self, instance):
        # user_obj = RateInfo.objects.filter(id=instance.proxy)[0]
        channelid = instance.channel_id
        userid = instance.user_id
        rate_queryset = RateInfo.objects.filter(channel_id=channelid, user_id=userid)
        if rate_queryset:
            return rate_queryset[0].rate
        return '加载中'

    # def get_username(self, instance):
    #     user_obj = UserProfile.objects.filter(id=instance.proxy)[0]
    #     return user_obj.username

    def get_device(self, instance):
        device_obj = DeviceInfo.objects.filter(id=instance.device_id)[0]
        return device_obj.device_name

    def get_channel(self, instance):
        channel_obj = channelInfo.objects.filter(id=instance.channel_id)[0]
        return channel_obj.channel_name

    class Meta:
        model = OrderInfo
        fields = '__all__'


class AdminWithDrawInfoDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    user = serializers.CharField(read_only=True, required=False)
    proxy_name = serializers.SerializerMethodField(read_only=True)
    bank = serializers.SerializerMethodField(label='绑定的用户', required=False)
    receive_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    def get_proxy_name(self, instance):
        user_q = UserProfile.objects.filter(id=instance.user_id)
        proxy_q = UserProfile.objects.filter(id=user_q[0].proxy_id)
        if proxy_q:
            return proxy_q[0].username
        return '加载中'

    def get_bank(self, obj):
        userqueryset = WithDrawBankInfo.objects.filter(id=obj.bank_id)
        obj = UserWithDrawBankListSerializer(userqueryset[0])
        return obj.data

    class Meta:
        model = WithDrawInfo
        fields = '__all__'


class AdminNoticeInfoDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = NoticeInfo
        fields = '__all__'


class AdminCountDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    user_num = serializers.SerializerMethodField()
    the_channelid = 0

    def get_user_num(self, instance):
        channelid = self.context['request'].query_params.get('channelid', None)
        if channelid:
            if not re.match(r'^([1-9]\d*$)', str(channelid)):
                raise serializers.ValidationError('channelid参数错误')
        self.the_channelid = channelid
        number = UserProfile.objects.filter(proxy_id=instance.id).count()
        return number

    device_num_on = serializers.SerializerMethodField()

    def get_device_num_on(self, instance):
        number = DeviceInfo.objects.filter(user_id=instance.id, is_active=True).count()
        return number

    device_num_all = serializers.SerializerMethodField()

    def get_device_num_all(self, instance):
        number = DeviceInfo.objects.filter(user_id=instance.id).count()
        return number

    # 小时 datetime.datetime.now()-datetime.timedelta(hours=1)
    hour_total_num = serializers.SerializerMethodField(read_only=True)

    def get_hour_total_num(self, obj):
        a = OrderInfo.objects.filter(proxy=obj.id,
                                     add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        return a.count()

    # 小时 成功数
    hour_success_num = serializers.SerializerMethodField(read_only=True)

    def get_hour_success_num(self, obj):
        a = OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                     proxy=obj.id,
                                     add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        return a.count()

    # 小时总金额
    hour_money_all = serializers.SerializerMethodField(read_only=True)

    def get_hour_money_all(self, obj):
        a = OrderInfo.objects.filter(proxy=obj.id,
                                     add_time__gte=datetime.datetime.now() - datetime.timedelta(
                                         hours=1))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    # 小时成功金额
    hour_money_success = serializers.SerializerMethodField(read_only=True)

    def get_hour_money_success(self, obj):
        a = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), proxy=obj.id,
            add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    # 今天
    # 今天 datetime.datetime.now()-datetime.timedelta(hours=1)
    today_total_num = serializers.SerializerMethodField(read_only=True)

    def get_today_total_num(self, obj):
        a = OrderInfo.objects.filter(proxy=obj.id,
                                     add_time__gte=time.strftime('%Y-%m-%d',
                                                                 time.localtime(time.time())))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)

        return a.count()

    # 今天 成功数
    today_success_num = serializers.SerializerMethodField(read_only=True)

    def get_today_success_num(self, obj):
        a = OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                     proxy=obj.id,
                                     add_time__gte=time.strftime('%Y-%m-%d',
                                                                 time.localtime(time.time())))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        return a.count()

    # 今天总金额
    today_money_all = serializers.SerializerMethodField(read_only=True)

    def get_today_money_all(self, obj):

        a = OrderInfo.objects.filter(proxy=obj.id,
                                     add_time__gte=time.strftime('%Y-%m-%d',
                                                                 time.localtime(
                                                                     time.time())))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    # 今天成功金额
    today_money_success = serializers.SerializerMethodField(read_only=True)

    def get_today_money_success(self, obj):

        a = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), proxy=obj.id,
            add_time__gte=time.strftime('%Y-%m-%d', time.localtime(time.time())))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    # 昨天
    # 昨天 datetime.datetime.now()-datetime.timedelta(hours=1)
    yesterday_total_num = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_total_num(self, obj):
        a = OrderInfo.objects.filter(proxy=obj.id,
                                     add_time__gte=(datetime.datetime.now() - datetime.timedelta(
                                         days=1)).strftime(
                                         '%Y-%m-%d'),
                                     add_time__lte=time.strftime('%Y-%m-%d',
                                                                 time.localtime(time.time())))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)

        return a.count()

    # 昨天 成功数
    yesterday_success_num = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_success_num(self, obj):
        a = OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                     proxy=obj.id,
                                     add_time__range=(
                                         (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
                                             '%Y-%m-%d'),
                                         time.strftime('%Y-%m-%d', time.localtime(time.time()))))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)

        return a.count()

    # 昨天总金额
    yesterday_money_all = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_money_all(self, obj):
        a = OrderInfo.objects.filter(proxy=obj.id,
                                     add_time__range=(
                                         (datetime.datetime.now() - datetime.timedelta(
                                             days=1)).strftime(
                                             '%Y-%m-%d'),
                                         time.strftime('%Y-%m-%d',
                                                       time.localtime(time.time()))))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    # 昨天成功金额
    yesterday_money_success = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_money_success(self, obj):
        a = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), proxy=obj.id,
            add_time__range=((datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                             time.strftime('%Y-%m-%d', time.localtime(time.time()))))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    # 当月
    # 当月 datetime.datetime.now()-datetime.timedelta(hours=1)
    month_total_num = serializers.SerializerMethodField(read_only=True)

    def get_month_total_num(self, obj):
        a = OrderInfo.objects.filter(proxy=obj.id,
                                     add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)

        return a.count()

    # 当月 成功数
    month_success_num = serializers.SerializerMethodField(read_only=True)

    def get_month_success_num(self, obj):
        a = OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                     proxy=obj.id,
                                     add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30))

        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)

        return a.count()

    #
    # 当月总金额
    month_money_all = serializers.SerializerMethodField(read_only=True)

    def get_month_money_all(self, obj):
        a = OrderInfo.objects.filter(proxy=obj.id,
                                     add_time__gte=(datetime.datetime.now() - datetime.timedelta(
                                         days=30)))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    #
    # 当月成功金额
    month_money_success = serializers.SerializerMethodField(read_only=True)

    def get_month_money_success(self, obj):
        a = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), proxy=obj.id,
            add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'add_time', 'user_num', 'device_num_on', 'device_num_all', 'hour_total_num',
                  'hour_success_num', 'hour_money_all', 'hour_money_success', 'today_total_num',
                  'today_success_num', 'today_money_all', 'today_money_success', 'yesterday_total_num',
                  'yesterday_success_num', 'yesterday_money_all', 'yesterday_money_success',
                  'month_total_num',
                  'month_success_num', 'month_money_all', 'month_money_success']


class AdminRateInfoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateInfo
        fields = ['rate', 'channel_id']


class AdminRateInfoListDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    # channel_name = serializers.SerializerMethodField(read_only=True)
    channel = serializers.CharField(read_only=True)
    # def get_channel_name(self, instance):
    #     channelInfo.objects.filter(id=instance.channel_id)
    #     return '1'
    class Meta:
        model = RateInfo
        fields = '__all__'


class AdminRateInfoputDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    user = serializers.CharField(read_only=True)
    mapid = serializers.IntegerField(write_only=True, required=False)
    channel = serializers.CharField(required=False)
    def validate_mapid(self, data):
        if not channelInfo.objects.filter(id=data):
            raise serializers.ValidationError('绑定通道不存在')
        return data

    class Meta:
        model = RateInfo
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=RateInfo.objects.all(),
                fields=('channel', 'user')
            )
        ]


class AdminCUserDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    proxy_name = serializers.SerializerMethodField(read_only=True)
    the_channelid = 0

    def get_proxy_name(self, instance):
        channelid = self.context['request'].query_params.get('channelid', None)
        if channelid:
            if not re.match(r'^([1-9]\d*$)', str(channelid)):
                raise serializers.ValidationError('channelid参数错误')
        self.the_channelid = channelid
        proxy_q = UserProfile.objects.filter(id=instance.proxy_id)
        if proxy_q:
            return proxy_q[0].username
        return '加载中'

    rate = serializers.SerializerMethodField()

    def get_rate(self, instance):
        rate_list = []
        rate_queryset = RateInfo.objects.filter(user_id=instance.id)
        if rate_queryset:
            for r in rate_queryset:
                if r.is_map:
                    s = AdminRateInfoDetailSerializer(r)
                    rate_list.append(s.data)
                else:
                    s = AdminRateInfoDetailSerializer(r)
                    rate_list.append(s.data)
            return rate_list
        return []

    # 小时 datetime.datetime.now()-datetime.timedelta(hours=1)
    hour_total_num = serializers.SerializerMethodField(read_only=True)

    def get_hour_total_num(self, obj):
        a = OrderInfo.objects.filter(user_id=obj.id,
                                     add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        return a.count()

    # 小时 成功数
    hour_success_num = serializers.SerializerMethodField(read_only=True)

    def get_hour_success_num(self, obj):
        a = OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                     user_id=obj.id,
                                     add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        return a.count()

    # 小时总金额
    hour_money_all = serializers.SerializerMethodField(read_only=True)

    def get_hour_money_all(self, obj):
        a = OrderInfo.objects.filter(user_id=obj.id,
                                     add_time__gte=datetime.datetime.now() - datetime.timedelta(
                                         hours=1))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    # 小时成功金额
    hour_money_success = serializers.SerializerMethodField(read_only=True)

    def get_hour_money_success(self, obj):
        a = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), user_id=obj.id,
            add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    # 今天
    # 今天 datetime.datetime.now()-datetime.timedelta(hours=1)
    today_total_num = serializers.SerializerMethodField(read_only=True)

    def get_today_total_num(self, obj):
        a = OrderInfo.objects.filter(user_id=obj.id,
                                     add_time__gte=time.strftime('%Y-%m-%d',
                                                                 time.localtime(time.time())))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)

        return a.count()

    # 今天 成功数
    today_success_num = serializers.SerializerMethodField(read_only=True)

    def get_today_success_num(self, obj):
        a = OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                     user_id=obj.id,
                                     add_time__gte=time.strftime('%Y-%m-%d',
                                                                 time.localtime(time.time())))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        return a.count()

    # 今天总金额
    today_money_all = serializers.SerializerMethodField(read_only=True)

    def get_today_money_all(self, obj):

        a = OrderInfo.objects.filter(user_id=obj.id,
                                     add_time__gte=time.strftime('%Y-%m-%d',
                                                                 time.localtime(
                                                                     time.time())))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    # 今天成功金额
    today_money_success = serializers.SerializerMethodField(read_only=True)

    def get_today_money_success(self, obj):

        a = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), user_id=obj.id,
            add_time__gte=time.strftime('%Y-%m-%d', time.localtime(time.time())))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    # 昨天
    # 昨天 datetime.datetime.now()-datetime.timedelta(hours=1)
    yesterday_total_num = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_total_num(self, obj):
        a = OrderInfo.objects.filter(user_id=obj.id,
                                     add_time__gte=(datetime.datetime.now() - datetime.timedelta(
                                         days=1)).strftime(
                                         '%Y-%m-%d'),
                                     add_time__lte=time.strftime('%Y-%m-%d',
                                                                 time.localtime(time.time())))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)

        return a.count()

    # 昨天 成功数
    yesterday_success_num = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_success_num(self, obj):
        a = OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                     user_id=obj.id,
                                     add_time__range=(
                                         (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
                                             '%Y-%m-%d'),
                                         time.strftime('%Y-%m-%d', time.localtime(time.time()))))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)

        return a.count()

    # 昨天总金额
    yesterday_money_all = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_money_all(self, obj):
        a = OrderInfo.objects.filter(user_id=obj.id,
                                     add_time__range=(
                                         (datetime.datetime.now() - datetime.timedelta(
                                             days=1)).strftime(
                                             '%Y-%m-%d'),
                                         time.strftime('%Y-%m-%d',
                                                       time.localtime(time.time()))))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    # 昨天成功金额
    yesterday_money_success = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_money_success(self, obj):
        a = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), user_id=obj.id,
            add_time__range=((datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                             time.strftime('%Y-%m-%d', time.localtime(time.time()))))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    # 当月
    # 当月 datetime.datetime.now()-datetime.timedelta(hours=1)
    month_total_num = serializers.SerializerMethodField(read_only=True)

    def get_month_total_num(self, obj):
        a = OrderInfo.objects.filter(user_id=obj.id,
                                     add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)

        return a.count()

    # 当月 成功数
    month_success_num = serializers.SerializerMethodField(read_only=True)

    def get_month_success_num(self, obj):
        a = OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                     user_id=obj.id,
                                     add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30))

        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)

        return a.count()

    #
    # 当月总金额
    month_money_all = serializers.SerializerMethodField(read_only=True)

    def get_month_money_all(self, obj):
        a = OrderInfo.objects.filter(user_id=obj.id,
                                     add_time__gte=(datetime.datetime.now() - datetime.timedelta(
                                         days=30)))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    #
    # 当月成功金额
    month_money_success = serializers.SerializerMethodField(read_only=True)

    def get_month_money_success(self, obj):
        a = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), user_id=obj.id,
            add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30))
        if self.the_channelid:
            a = a.filter(channel_id=self.the_channelid)
        b = a.aggregate(
            real_money=Sum('real_money')).get('real_money')
        if not b:
            return 0
        return b

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'money', 'proxy_name', 'rate', 'add_time', 'hour_total_num',
                  'hour_success_num', 'hour_money_all', 'hour_money_success', 'today_total_num',
                  'today_success_num', 'today_money_all', 'today_money_success', 'yesterday_total_num',
                  'yesterday_success_num', 'yesterday_money_all', 'yesterday_money_success',
                  'month_total_num',
                  'month_success_num', 'month_money_all', 'month_money_success']


class AdminCCRetrieveSerializer(serializers.ModelSerializer):
    channelid = serializers.IntegerField(write_only=True, required=False)
    userid = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = UserProfile
        fields = ['userid', 'channelid']


class ReleaseSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField(write_only=True,required=True)
    end_time = serializers.DateTimeField(write_only=True,required=True)
    dele_type = serializers.CharField(write_only=True,required=True)
    safe_code = serializers.CharField(write_only=True,required=True)
    proxy_id = serializers.IntegerField(write_only=True,required=True)
    def validate(self, attrs):
        s_time = attrs.get('start_time')
        e_time = attrs.get('end_time')
        dele_type = attrs.get('dele_type')
        if s_time:
            if not re.match(r'(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})', str(s_time)):
                raise serializers.ValidationError('时间格式错误，请重新输入')
        if e_time:
            if not re.match(r'(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})', str(e_time)):
                raise serializers.ValidationError('时间格式错误，请重新输入')
        if str(dele_type) not in ['order', 'money', 'log']:
            raise serializers.ValidationError('传值错误')
        return attrs


class AdminCDataOrderSerializer(serializers.Serializer):
    pass


class OrderChartListSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = OrderInfo
        fields = ['add_time', 'real_money', 'channel']

class AdminLogListInfoSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    whodo = serializers.SerializerMethodField()
    log_type = serializers.SerializerMethodField()

    def get_whodo(self, obj):
        id = obj.user_id
        user_queryset = UserProfile.objects.filter(id=id)
        if user_queryset:
            return user_queryset[0].username
        return ''

    def get_log_type(self, obj):
        return eval('obj.get_log_type_display()')

    class Meta:
        model = LogInfo
        fields = '__all__'

class AdminLogInfoSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = LogInfo
        fields = '__all__'