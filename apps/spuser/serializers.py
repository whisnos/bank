import datetime
import re
import time

from django.db.models import Q, Sum
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from channel.models import channelInfo
from proxy.models import DeviceInfo, RateInfo
from spuser.models import NoticeInfo
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


class AdminProxyUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(label='密码', required=False, allow_blank=False, min_length=6,
                                     style={'input_type': 'password'}, help_text='密码')
    password2 = serializers.CharField(label='密码', required=False, allow_blank=False, write_only=True, min_length=6,
                                      style={'input_type': 'password'}, help_text='密码')
    safe_code = serializers.CharField(label='操作密码', required=False, allow_blank=False, write_only=True, min_length=6,
                                      style={'input_type': 'password'}, help_text='密码')
    safe_code2 = serializers.CharField(label='操作密码', required=False, allow_blank=False, write_only=True, min_length=6,
                                       style={'input_type': 'password'}, help_text='密码')

    class Meta:
        model = UserProfile
        fields = ['password', 'password2', 'safe_code', 'safe_code2']


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
        if str(attrs.get('is_active')) not in ['True', 'False', 'None']:
            raise serializers.ValidationError('传值错误')
        return attrs

    class Meta:
        model = UserProfile
        fields = ['is_active', 'auth_code', 'password', 'password2']
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
    channel = serializers.SerializerMethodField()
    device = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
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

    def get_username(self, instance):
        user_obj = UserProfile.objects.filter(id=instance.proxy)[0]
        return user_obj.username

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
    user = serializers.SerializerMethodField(label='绑定的用户', required=False)
    bank = serializers.SerializerMethodField(label='绑定的用户', required=False)

    def get_user(self, obj):
        userqueryset = UserProfile.objects.filter(id=obj.user_id)
        obj = userqueryset[0].username
        return obj

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

    # 小时 datetime.datetime.now()-datetime.timedelta(hours=1)
    hour_total_num = serializers.SerializerMethodField(read_only=True)

    def get_hour_total_num(self, obj):
        a = OrderInfo.objects.filter(proxy=obj.id,
                                     add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1)).count()

        return a

    # 小时 成功数
    hour_success_num = serializers.SerializerMethodField(read_only=True)

    def get_hour_success_num(self, obj):
        return OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                        proxy=obj.id,
                                        add_time__gte=datetime.datetime.now() - datetime.timedelta(hours=1)).count()

    # 小时总金额
    hour_money_all = serializers.SerializerMethodField(read_only=True)

    def get_hour_money_all(self, obj):
        order_queryset = OrderInfo.objects.filter(proxy=obj.id,
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
            (Q(pay_status=1) | Q(pay_status=3)), proxy=obj.id,
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
        return OrderInfo.objects.filter(proxy=obj.id,
                                        add_time__gte=time.strftime('%Y-%m-%d',
                                                                    time.localtime(time.time()))).count()

    # 今天 成功数
    today_success_num = serializers.SerializerMethodField(read_only=True)

    def get_today_success_num(self, obj):
        return OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                        proxy=obj.id,
                                        add_time__gte=time.strftime('%Y-%m-%d',
                                                                    time.localtime(time.time()))).count()

    # 今天总金额
    today_money_all = serializers.SerializerMethodField(read_only=True)

    def get_today_money_all(self, obj):
        order_queryset = OrderInfo.objects.filter(proxy=obj.id,
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
            (Q(pay_status=1) | Q(pay_status=3)), proxy=obj.id,
            add_time__gte=time.strftime('%Y-%m-%d', time.localtime(time.time()))).aggregate(
            real_money=Sum('real_money'))
        if not order_queryset.get('real_money', '0'):
            return '0'
        return order_queryset.get('real_money', 0)

    # 昨天
    # 昨天 datetime.datetime.now()-datetime.timedelta(hours=1)
    yesterday_total_num = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_total_num(self, obj):
        return OrderInfo.objects.filter(proxy=obj.id,
                                        add_time__gte=(datetime.datetime.now() - datetime.timedelta(
                                            days=1)).strftime(
                                            '%Y-%m-%d'),
                                        add_time__lte=time.strftime('%Y-%m-%d',
                                                                    time.localtime(time.time()))).count()

    # 昨天 成功数
    yesterday_success_num = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_success_num(self, obj):
        return OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                        proxy=obj.id,
                                        add_time__range=(
                                            (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
                                                '%Y-%m-%d'),
                                            time.strftime('%Y-%m-%d', time.localtime(time.time())))).count()

    # 昨天总金额
    yesterday_money_all = serializers.SerializerMethodField(read_only=True)

    def get_yesterday_money_all(self, obj):
        order_queryset = OrderInfo.objects.filter(proxy=obj.id,
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
            (Q(pay_status=1) | Q(pay_status=3)), proxy=obj.id,
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
        return OrderInfo.objects.filter(proxy=obj.id,
                                        add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30)).count()

    # 当月 成功数
    month_success_num = serializers.SerializerMethodField(read_only=True)

    def get_month_success_num(self, obj):
        return OrderInfo.objects.filter((Q(pay_status=1) | Q(pay_status=3)),
                                        proxy=obj.id,
                                        add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30)).count()

    #
    # 当月总金额
    month_money_all = serializers.SerializerMethodField(read_only=True)

    def get_month_money_all(self, obj):
        order_queryset = OrderInfo.objects.filter(proxy=obj.id,
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
            (Q(pay_status=1) | Q(pay_status=3)), proxy=obj.id,
            add_time__gte=datetime.datetime.now() - datetime.timedelta(days=30)).aggregate(
            real_money=Sum('real_money'))
        if not order_queryset.get('real_money', '0'):
            return '0'
        return order_queryset.get('real_money', 0)

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


class AdminCUserDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    proxy_name = serializers.SerializerMethodField(read_only=True)

    def get_proxy_name(self, instance):
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
        fields = ['id', 'username', 'money', 'proxy_name', 'rate', 'add_time', 'hour_total_num',
                  'hour_success_num', 'hour_money_all', 'hour_money_success', 'today_total_num',
                  'today_success_num', 'today_money_all', 'today_money_success', 'yesterday_total_num',
                  'yesterday_success_num', 'yesterday_money_all', 'yesterday_money_success',
                  'month_total_num',
                  'month_success_num', 'month_money_all', 'month_money_success']


class ReleaseSerializer(serializers.Serializer):
    s_time = serializers.DateTimeField(write_only=True)
    e_time = serializers.DateTimeField(write_only=True)
    dele_type = serializers.CharField(write_only=True)
    safe_code = serializers.CharField(write_only=True)

    def validate(self, attrs):
        s_time = attrs.get('s_time')
        e_time = attrs.get('e_time')
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


class CDataOrderSerializer(serializers.Serializer):
    s_time = serializers.DateTimeField(write_only=True,required=False)
    e_time = serializers.DateTimeField(write_only=True,required=False)
    # success_money=serializers.SerializerMethodField()
    # def get_success_money(self, instance):
    #     print('a',instance)
    #
    #     return 'a'
    #
    # def validate(self, attrs):
    #     print('attrs',attrs)
    #     s_time = attrs.get('s_time')
    #     e_time = attrs.get('e_time')
    #     if s_time:
    #         if not re.match(r'(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})', str(s_time)):
    #             raise serializers.ValidationError('时间格式错误，请重新输入')
    #     if e_time:
    #         if not re.match(r'(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})', str(e_time)):
    #             raise serializers.ValidationError('时间格式错误，请重新输入')
    #
    #     return attrs
    # class Meta:
    #     model = OrderInfo
    #     fields = ['success_money']