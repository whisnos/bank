import datetime
import time

from django.db.models import Sum, Q
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

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
    channel=serializers.CharField()
    class Meta:
        model = DeviceChannelInfo
        fields = '__all__'

class ProxyDeviceInfoDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    channel=serializers.SerializerMethodField()
    password=serializers.CharField(read_only=True)
    def get_channel(self, instance):
        a=[]
        device_q=DeviceChannelInfo.objects.filter(device_id=instance.id).order_by('-add_time')
        for d in device_q:
            serializer=ProxyDChannelDetailSerializer(d)
            a.append(serializer.data)
        return a
    # 小时 datetime.datetime.now()-datetime.timedelta(hours=1)
    hour_total_num = serializers.SerializerMethodField(read_only=True)
    def get_hour_total_num(self, obj):
        return OrderInfo.objects.filter(device_id=obj.id, add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1)).count()
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
        fields = ['id', 'device_name','password','channel','is_active','add_time', 'hour_total_num',
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
    device_name = serializers.SerializerMethodField(read_only=True)
    def get_device_name(self, instance):
        obj_q=DeviceInfo.objects.filter(id=instance.device)
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


class ProxyCountDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
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
                                     add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1)).count()

        return a

    # 小时 成功数
    hour_success_num = serializers.SerializerMethodField(read_only=True)

    def get_hour_success_num(self, obj):
        return OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                        user_id=obj.id,
                                        add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1)).count()

    # 小时总金额
    hour_money_all = serializers.SerializerMethodField(read_only=True)

    def get_hour_money_all(self, obj):
        order_queryset = OrderInfo.objects.filter(user_id=obj.id,
                                                  add_time__gte=datetime.datetime.now() - datetime.timedelta(
                                                      hours=1)).aggregate(
            real_money=Sum('real_money'))
        if not order_queryset.get('real_money', '0'):
            return '0'
        return order_queryset.get('real_money', '0')

    # 小时成功金额
    hour_money_success = serializers.SerializerMethodField(read_only=True)

    def get_hour_money_success(self, obj):
        # userid_list = self.make_userid_list(obj)
        order_queryset = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), user_id=obj.id,
            add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1)).aggregate(
            real_money=Sum('real_money'))
        if not order_queryset.get('real_money', '0'):
            return '0'
        return order_queryset.get('real_money', 0)

    # 今天
    # 今天 datetime.datetime.now()-datetime.timedelta(hours=1)
    today_total_num = serializers.SerializerMethodField(read_only=True)

    def get_today_total_num(self, obj):
        # userid_list = self.make_userid_list(obj)
        return OrderInfo.objects.filter(user_id=obj.id,
                                        add_time__gte=time.strftime('%Y-%m-%d',
                                                                    time.localtime(time.time()))).count()

    # 今天 成功数
    today_success_num = serializers.SerializerMethodField(read_only=True)

    def get_today_success_num(self, obj):
        return OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                        user_id=obj.id,
                                        add_time__gte=time.strftime('%Y-%m-%d',
                                                                    time.localtime(time.time()))).count()

    # 今天总金额
    today_money_all = serializers.SerializerMethodField(read_only=True)

    def get_today_money_all(self, obj):
        order_queryset = OrderInfo.objects.filter(user_id=obj.id,
                                                  add_time__gte=time.strftime('%Y-%m-%d',
                                                                              time.localtime(
                                                                                  time.time()))).aggregate(
            real_money=Sum('real_money'))
        if not order_queryset.get('real_money', '0'):
            return '0'
        return order_queryset.get('real_money', 0)

    # 今天成功金额
    today_money_success = serializers.SerializerMethodField(read_only=True)

    def get_today_money_success(self, obj):
        order_queryset = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), user_id=obj.id,
            add_time__gte=time.strftime('%Y-%m-%d', time.localtime(time.time()))).aggregate(
            real_money=Sum('real_money'))
        if not order_queryset.get('real_money', '0'):
            return '0'
        return order_queryset.get('real_money', 0)

    # 昨天
    # 昨天 datetime.datetime.now()-datetime.timedelta(hours=1)
    yesterday_total_num = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_total_num(self, obj):
        return OrderInfo.objects.filter(user_id=obj.id,
                                        add_time__gte=(datetime.datetime.now() - datetime.timedelta(
                                            days=1)).strftime(
                                            '%Y-%m-%d'),
                                        add_time__lte=time.strftime('%Y-%m-%d',
                                                                    time.localtime(time.time()))).count()

    # 昨天 成功数
    yesterday_success_num = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_success_num(self, obj):
        return OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                        user_id=obj.id,
                                        add_time__range=(
                                            (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
                                                '%Y-%m-%d'),
                                            time.strftime('%Y-%m-%d', time.localtime(time.time())))).count()

    # 昨天总金额
    yesterday_money_all = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_money_all(self, obj):
        order_queryset = OrderInfo.objects.filter(user_id=obj.id,
                                                  add_time__range=(
                                                      (datetime.datetime.now() - datetime.timedelta(
                                                          days=1)).strftime(
                                                          '%Y-%m-%d'),
                                                      time.strftime('%Y-%m-%d',
                                                                    time.localtime(time.time())))).aggregate(
            real_money=Sum('real_money'))
        if not order_queryset.get('real_money', '0'):
            return '0'
        return order_queryset.get('real_money', 0)

    # 昨天成功金额
    yesterday_money_success = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_money_success(self, obj):
        order_queryset = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), user_id=obj.id,
            add_time__range=((datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                             time.strftime('%Y-%m-%d', time.localtime(time.time())))).aggregate(
            real_money=Sum('real_money'))
        if not order_queryset.get('real_money', '0'):
            return '0'
        return order_queryset.get('real_money', 0)

    # 当月
    # 当月 datetime.datetime.now()-datetime.timedelta(hours=1)
    month_total_num = serializers.SerializerMethodField(read_only=True)

    def get_month_total_num(self, obj):
        return OrderInfo.objects.filter(user_id=obj.id,
                                        add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30)).count()

    # 当月 成功数
    month_success_num = serializers.SerializerMethodField(read_only=True)

    def get_month_success_num(self, obj):
        return OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                        user_id=obj.id,
                                        add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30)).count()

    #
    # 当月总金额
    month_money_all = serializers.SerializerMethodField(read_only=True)

    def get_month_money_all(self, obj):
        order_queryset = OrderInfo.objects.filter(user_id=obj.id,
                                                  add_time__gte=(datetime.datetime.now() - datetime.timedelta(
                                                      days=30))).aggregate(
            real_money=Sum('real_money'))
        if not order_queryset.get('real_money', '0'):
            return '0'
        return order_queryset.get('real_money', 0)

    #
    # 当月成功金额
    month_money_success = serializers.SerializerMethodField(read_only=True)

    def get_month_money_success(self, obj):
        order_queryset = OrderInfo.objects.filter(
            (Q(pay_status=1) | Q(pay_status=3)), user_id=obj.id,
            add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30)).aggregate(
            real_money=Sum('real_money'))
        if not order_queryset.get('real_money', '0'):
            return '0'
        return order_queryset.get('real_money', 0)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'level', 'uid', 'auth_code', 'money', 'is_active', 'mobile', 'web_url',
                  'proxy_id','rate', 'add_time', 'hour_total_num',
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

