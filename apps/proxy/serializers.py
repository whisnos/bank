import datetime
import re
import time

from django.db.models import Sum, Q
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from channel.models import AlipayInfo
from proxy.models import RateInfo, DeviceInfo, ReceiveBankInfo, DeviceChannelInfo
from spuser.serializers import AdminRateInfoDetailSerializer
from trade.models import OrderInfo, WithDrawInfo, WithDrawBankInfo
from user.models import UserProfile
from user.serializers import UserWithDrawBankListSerializer


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
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    channel = serializers.CharField(read_only=True)

    class Meta:
        model = RateInfo
        fields = '__all__'


class UpdateRateInfoSerializer(serializers.ModelSerializer):
    rate = serializers.DecimalField(max_digits=4, decimal_places=3, required=False)
    is_map = serializers.BooleanField(required=False)
    mapid = serializers.IntegerField(required=False)

    def validate(self, attrs):
        print('attrs', attrs)
        print("attrs.get('is_map')", attrs.get('is_map'))
        if str(attrs.get('is_map')) not in ['True', 'False', 'None']:
            raise serializers.ValidationError('传值错误')
        return attrs

    class Meta:
        model = RateInfo
        fields = ['rate', 'is_map', 'mapid']


class ProxyWithDrawInfoDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    receive_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    user = serializers.CharField(read_only=True)
    bank = serializers.SerializerMethodField(label='绑定的用户', required=False)

    def get_bank(self, obj):
        userqueryset = WithDrawBankInfo.objects.filter(id=obj.bank_id)
        obj = UserWithDrawBankListSerializer(userqueryset[0])
        return obj.data

    class Meta:
        model = WithDrawInfo
        fields = '__all__'


class ProxyWithDrawInfoUpdateDetailSerializer(serializers.ModelSerializer):
    remark = serializers.CharField(required=False)
    withdraw_status = serializers.IntegerField(required=False)

    class Meta:
        model = WithDrawInfo
        fields = ['withdraw_status', 'remark']


class ProxyDChannelDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    channel = serializers.CharField()

    class Meta:
        model = DeviceChannelInfo
        fields = '__all__'


class ProxyDeviceInfoDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    channel = serializers.SerializerMethodField()
    password = serializers.CharField(read_only=True)

    def get_channel(self, instance):
        a = []
        device_q = DeviceChannelInfo.objects.filter(device_id=instance.id).order_by('-add_time')
        for d in device_q:
            serializer = ProxyDChannelDetailSerializer(d)
            a.append(serializer.data)
        return a

    # 小时 datetime.datetime.now()-datetime.timedelta(hours=1)
    hour_total_num = serializers.SerializerMethodField(read_only=True)

    def get_hour_total_num(self, obj):
        return OrderInfo.objects.filter(device_id=obj.id,
                                        add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1)).count()

    # 小时 成功数
    hour_success_num = serializers.SerializerMethodField(read_only=True)

    def get_hour_success_num(self, obj):
        return OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                        device_id=obj.id,
                                        add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1)).count()

    # 小时总金额
    hour_money_all = serializers.SerializerMethodField(read_only=True)

    def get_hour_money_all(self, obj):
        order_queryset = OrderInfo.objects.filter(device_id=obj.id,
                                                  add_time__gte=datetime.datetime.now() - datetime.timedelta(
                                                      hours=1)).aggregate(
            real_money=Sum('real_money'))
        return order_queryset.get('real_money', '0')

    # 小时成功金额
    hour_money_success = serializers.SerializerMethodField(read_only=True)

    def get_hour_money_success(self, obj):
        # userid_list = self.make_userid_list(obj)
        order_queryset = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), device_id=obj.id,
            add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1)).aggregate(
            real_money=Sum('real_money'))
        return order_queryset.get('real_money', '0')

    # 今天
    # 今天 datetime.datetime.now()-datetime.timedelta(hours=1)
    today_total_num = serializers.SerializerMethodField(read_only=True)

    def get_today_total_num(self, obj):
        # userid_list = self.make_userid_list(obj)
        return OrderInfo.objects.filter(device_id=obj.id,
                                        add_time__gte=time.strftime('%Y-%m-%d',
                                                                    time.localtime(time.time()))).count()

    # 今天 成功数
    today_success_num = serializers.SerializerMethodField(read_only=True)

    def get_today_success_num(self, obj):
        return OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                        device_id=obj.id,
                                        add_time__gte=time.strftime('%Y-%m-%d',
                                                                    time.localtime(time.time()))).count()

    # 今天总金额
    today_money_all = serializers.SerializerMethodField(read_only=True)

    def get_today_money_all(self, obj):
        order_queryset = OrderInfo.objects.filter(device_id=obj.id,
                                                  add_time__gte=time.strftime('%Y-%m-%d',
                                                                              time.localtime(
                                                                                  time.time()))).aggregate(
            real_money=Sum('real_money'))
        return order_queryset.get('real_money', 0)

    # 今天成功金额
    today_money_success = serializers.SerializerMethodField(read_only=True)

    def get_today_money_success(self, obj):
        order_queryset = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), device_id=obj.id,
            add_time__gte=time.strftime('%Y-%m-%d', time.localtime(time.time()))).aggregate(
            real_money=Sum('real_money'))
        return order_queryset.get('real_money', 0)

    # 昨天
    # 昨天 datetime.datetime.now()-datetime.timedelta(hours=1)
    yesterday_total_num = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_total_num(self, obj):
        return OrderInfo.objects.filter(device_id=obj.id,
                                        add_time__gte=(datetime.datetime.now() - datetime.timedelta(
                                            days=1)).strftime(
                                            '%Y-%m-%d'),
                                        add_time__lte=time.strftime('%Y-%m-%d',
                                                                    time.localtime(time.time()))).count()

    # 昨天 成功数
    yesterday_success_num = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_success_num(self, obj):
        return OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                        device_id=obj.id,
                                        add_time__range=(
                                            (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
                                                '%Y-%m-%d'),
                                            time.strftime('%Y-%m-%d', time.localtime(time.time())))).count()

    # 昨天总金额
    yesterday_money_all = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_money_all(self, obj):
        order_queryset = OrderInfo.objects.filter(device_id=obj.id,
                                                  add_time__range=(
                                                      (datetime.datetime.now() - datetime.timedelta(
                                                          days=1)).strftime(
                                                          '%Y-%m-%d'),
                                                      time.strftime('%Y-%m-%d',
                                                                    time.localtime(time.time())))).aggregate(
            real_money=Sum('real_money'))
        return order_queryset.get('real_money', 0)

    # 昨天成功金额
    yesterday_money_success = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_money_success(self, obj):
        order_queryset = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), device_id=obj.id,
            add_time__range=((datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                             time.strftime('%Y-%m-%d', time.localtime(time.time())))).aggregate(
            real_money=Sum('real_money'))
        return order_queryset.get('real_money', 0)

    # 当月
    # 当月 datetime.datetime.now()-datetime.timedelta(hours=1)
    month_total_num = serializers.SerializerMethodField(read_only=True)

    def get_month_total_num(self, obj):
        return OrderInfo.objects.filter(device_id=obj.id,
                                        add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30)).count()

    # 当月 成功数
    month_success_num = serializers.SerializerMethodField(read_only=True)

    def get_month_success_num(self, obj):
        return OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                        device_id=obj.id,
                                        add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30)).count()

    #
    # 当月总金额
    month_money_all = serializers.SerializerMethodField(read_only=True)

    def get_month_money_all(self, obj):
        order_queryset = OrderInfo.objects.filter(device_id=obj.id,
                                                  add_time__gte=(datetime.datetime.now() - datetime.timedelta(
                                                      days=30))).aggregate(
            real_money=Sum('real_money'))
        return order_queryset.get('real_money', 0)

    #
    # 当月成功金额
    month_money_success = serializers.SerializerMethodField(read_only=True)

    def get_month_money_success(self, obj):
        order_queryset = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), device_id=obj.id,
            add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30)).aggregate(
            real_money=Sum('real_money'))
        return order_queryset.get('real_money', 0)

    class Meta:
        model = DeviceInfo
        fields = ['id', 'device_name', 'password', 'channel', 'is_active', 'add_time', 'auth_code', 'hour_total_num',
                  'hour_success_num', 'hour_money_all', 'hour_money_success', 'today_total_num',
                  'today_success_num', 'today_money_all', 'today_money_success', 'yesterday_total_num',
                  'yesterday_success_num', 'yesterday_money_all', 'yesterday_money_success',
                  'month_total_num',
                  'month_success_num', 'month_money_all', 'month_money_success']


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
                                     max_length=15,
                                     style={'input_type': 'password'}, help_text='密码')
    password2 = serializers.CharField(label='确认密码', write_only=True, required=True, allow_blank=False, min_length=6,
                                      max_length=15,
                                      style={'input_type': 'password'}, help_text='重复密码')
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate(self, attrs):
        print('attrs', attrs)
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次输入密码不一致')
        return attrs

    class Meta:
        model = DeviceInfo
        fields = ['user', 'device_name', 'password', 'password2']


class ProxyReceiveBankInfoDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    device_name = serializers.SerializerMethodField(read_only=True)

    def get_device_name(self, instance):
        obj_q = DeviceInfo.objects.filter(id=instance.device)
        if not obj_q:
            return '暂无匹配设备'
        return obj_q[0].device_name

    class Meta:
        model = ReceiveBankInfo
        fields = '__all__'


class ProxyReceiveBankInfoRetriDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    device_name = serializers.SerializerMethodField(read_only=True)

    def get_device_name(self, instance):
        obj_q = DeviceInfo.objects.filter(id=instance.device)
        if not obj_q:
            return '暂无匹配设备'
        return obj_q[0].device_name

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
    username = serializers.CharField(label='收款人姓名', required=True, min_length=1, max_length=20, allow_blank=False,
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


class ProxyCountDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    rate = serializers.SerializerMethodField()
    the_channelid = 0

    def get_rate(self, instance):
        channelid = self.context['request'].query_params.get('channelid', None)
        if channelid:
            if not re.match(r'^([1-9]\d*$)', str(channelid)):
                raise serializers.ValidationError('channelid参数错误')
        self.the_channelid = channelid
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
        # userid_list = self.make_userid_list(obj)
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
        return OrderInfo.objects.filter(user_id=obj.id,
                                        add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30)).count()

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
        fields = ['id', 'username', 'level', 'uid', 'auth_code', 'money', 'is_active', 'mobile', 'web_url',
                  'proxy_id', 'rate', 'add_time', 'hour_total_num',
                  'hour_success_num', 'hour_money_all', 'hour_money_success', 'today_total_num',
                  'today_success_num', 'today_money_all', 'today_money_success', 'yesterday_total_num',
                  'yesterday_success_num', 'yesterday_money_all', 'yesterday_money_success',
                  'month_total_num',
                  'month_success_num', 'month_money_all', 'month_money_success']


class ProxyCODataSerializer(serializers.ModelSerializer):
    # add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    # username = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username']


class ProxyCODataRetrieveSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = UserProfile
        fields = ['add_time']


class CallBackOrderUpdateSeralizer(serializers.ModelSerializer):
    # add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    # channel = serializers.SerializerMethodField()
    # device = serializers.SerializerMethodField()
    # user = serializers.CharField(read_only=True,)
    # # pay_status = serializers.SerializerMethodField()
    # #
    # # def get_pay_status(self, instance):
    # #     return eval('instance.get_pay_status_display()')
    # rate = serializers.SerializerMethodField()
    #
    # def get_rate(self, instance):
    #     # user_obj = RateInfo.objects.filter(id=instance.proxy)[0]
    #     channelid = instance.channel_id
    #     userid = instance.user_id
    #     rate_queryset = RateInfo.objects.filter(channel_id=channelid, user_id=userid)
    #     if rate_queryset:
    #         return rate_queryset[0].rate
    #     return '加载中'
    #
    # # def get_username(self, instance):
    # #     user_obj = UserProfile.objects.filter(id=instance.proxy)[0]
    # #     return user_obj.username
    #
    # def get_device(self, instance):
    #     device_obj = DeviceInfo.objects.filter(id=instance.device_id)[0]
    #     return device_obj.device_name
    #
    # def get_channel(self, instance):
    #     channel_obj = channelInfo.objects.filter(id=instance.channel_id)[0]
    #     return channel_obj.channel_name

    class Meta:
        model = OrderInfo
        fields = ['pay_status']


class OrderGetSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    order_money = serializers.SerializerMethodField(read_only=True)

    # def get_order_money(self, instance):
    #     return int(instance.total_amount) * 100

    class Meta:
        model = OrderInfo
        fields = ['id', 'order_money']


class OrderUpdatePaySerializer(serializers.Serializer):
    auth_code = serializers.CharField(required=True)
    # class Meta:
    #     model = OrderInfo
    #     fields = ['auth_code']


class ProxyDCInfoSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = DeviceChannelInfo
        fields = '__all__'


class ProxyDCInfoUPSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True)
    channel = serializers.CharField(required=False, read_only=True)
    device = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = DeviceChannelInfo
        fields = '__all__'


class VerifyPaySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = '__all__'


class DeviceReceiveBankCreDetailSerializer(serializers.ModelSerializer):
    # user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    username = serializers.CharField(label='收款人姓名', required=True, min_length=1, max_length=20, allow_blank=False,
                                     help_text='用户名')
    card_number = serializers.CharField(required=True, validators=[
        UniqueValidator(queryset=ReceiveBankInfo.objects.all(), message='卡号不能重复')
    ], label='银行卡号')
    bank_type = serializers.CharField(required=True, label='银行类型')
    bank_mark = serializers.CharField(required=True, label='银行编号')
    bank_tel = serializers.CharField(required=True, label='银行电话')
    card_index = serializers.CharField(required=True, label='卡索引')

    # device = serializers.IntegerField(required=True, label='设备id')
    def validate(self, attrs):
        print('attrs', attrs)
        return attrs

    class Meta:
        model = ReceiveBankInfo
        fields = ['username', 'card_number', 'bank_type', 'bank_mark', 'bank_tel', 'card_index']


class ProxyAlipayInfoDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = AlipayInfo
        fields = '__all__'


class ProxyAlipayInfoPostSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, label='公司名')
    c_appid = serializers.CharField(required=True, label='appid', validators=[
        UniqueValidator(queryset=AlipayInfo.objects.all(), message='appid不能重复')])
    alipay_public_key = serializers.CharField(required=True, label='公钥')
    c_private_key = serializers.CharField(required=True, label='私钥')
    # add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = AlipayInfo
        fields = ['name', 'c_appid', 'alipay_public_key', 'c_private_key', 'user']


class ProxyAlipayInfoUpdateDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, label='公司名')
    c_appid = serializers.CharField(required=False, label='appid', validators=[
        UniqueValidator(queryset=AlipayInfo.objects.all(), message='appid不能重复')])
    alipay_public_key = serializers.CharField(required=False, label='公钥')
    c_private_key = serializers.CharField(required=False, label='私钥')
    is_active = serializers.BooleanField(required=False, label='是否激活')

    class Meta:
        model = AlipayInfo
        fields = ['name', 'c_appid', 'alipay_public_key', 'c_private_key', 'is_active']
