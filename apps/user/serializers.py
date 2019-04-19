import datetime
import re
import time

from django.db.models import Sum, Q
from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from proxy.models import RateInfo, DeviceInfo
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
    web_url = serializers.CharField(write_only=True, required=False, help_text='web_url')
    add_money = serializers.DecimalField(max_digits=7, decimal_places=2, help_text='加款', write_only=True,
                                         required=False)
    desc_money = serializers.DecimalField(max_digits=7, decimal_places=2, help_text='扣款', write_only=True,
                                          required=False)
    remark = serializers.CharField(write_only=True,required=False)
    class Meta:
        model = UserProfile
        fields = ['auth_code', 'password', 'password2', 'web_url', 'add_money', 'desc_money','remark']


class UpdateOnlyUserInfoSerializer(serializers.ModelSerializer):
    auth_code = serializers.CharField(write_only=True, required=False, )
    password2 = serializers.CharField(write_only=True, required=False, min_length=6,
                                      style={'input_type': 'password'}, )
    password = serializers.CharField(write_only=True, required=False, min_length=6,
                                     style={'input_type': 'password'}, help_text='密码')
    web_url = serializers.CharField(write_only=True, required=False, help_text='web_url')

    # add_money = serializers.DecimalField(max_digits=7, decimal_places=2, help_text='加款', write_only=True,
    #                                      required=False)
    # desc_money = serializers.DecimalField(max_digits=7, decimal_places=2, help_text='扣款', write_only=True,
    #                                       required=False)

    class Meta:
        model = UserProfile
        fields = ['auth_code', 'password', 'password2', 'web_url']


class ProxyUserCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(label='用户名', required=True, min_length=2, max_length=20, allow_blank=False,
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
    web_url = serializers.CharField(required=False,write_only=True,allow_blank=True,allow_null=True)
    # uid = serializers.CharField(label='uid', read_only=True, validators=[
    #     UniqueValidator(queryset=UserProfile.objects.all(), message='uid不能重复')
    # ], help_text='用户uid')
    # auth_code = serializers.CharField(label='授权码', read_only=True, validators=[
    #     UniqueValidator(queryset=UserProfile.objects.all(), message='授权码不能重复')
    # ], help_text='用户授权码')

    class Meta:
        model = UserProfile
        fields = ['username', 'password', 'password2', 'mobile','web_url']

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
    total_amount = serializers.FloatField(read_only=True)
    account_num = serializers.CharField(read_only=True)

    rate = serializers.SerializerMethodField()

    def get_rate(self, instance):
        channelid = instance.channel_id
        userid = instance.user_id
        rate_queryset = RateInfo.objects.filter(channel_id=channelid, user_id=userid)
        if rate_queryset:
            return rate_queryset[0].rate
        return '加载中'
    class Meta:
        model = OrderInfo
        # fields = ['id', 'user_id', 'username', 'pay_status', 'total_amount', 'order_no', 'pay_time', 'add_time',
        #           'order_id', 'account_num']
        fields = '__all__'


class UserWithDrawListSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    proxy_name = serializers.SerializerMethodField()
    bank = serializers.SerializerMethodField(label='绑定的用户', required=False)

    def get_bank(self, obj):
        userqueryset = WithDrawBankInfo.objects.filter(id=obj.bank_id)
        obj = UserWithDrawBankListSerializer(userqueryset[0])
        return obj.data

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
    bank = serializers.IntegerField(required=True, help_text='银行卡id')
    withdraw_money = serializers.IntegerField(write_only=True,required=True)
    safe_code = serializers.CharField(write_only=True,required=True)
    def validate(self, attrs):
        user = self.context['request'].user
        user_money = user.money
        if not re.match(
                r'(^[1-9]([0-9]{1,4})?(\.[0-9]{1,2})?$)|(^(0){1}$)|(^[0-9]\.[0-9]([0-9])?$)',
                str(attrs['withdraw_money'])):
            raise serializers.ValidationError('金额输入异常999')
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
    open_bank = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    bank_name = serializers.CharField(required=True)
    mobile = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate(self, attrs):
        print('attrs', attrs)
        return attrs

    class Meta:
        model = WithDrawBankInfo
        fields = '__all__'


class UserCountDetailSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

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

    # # 小时 成功率
    # hour_rate = serializers.SerializerMethodField(read_only=True)
    #
    # def get_hour_rate(self, obj):
    #     a = self.get_hour_success_num(obj)
    #     b = self.get_hour_total_num(obj)
    #     if b == 0 or a == 0:
    #         return '0%'
    #     return ('{:.2%}'.format(a / b))

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

    # 今天 成功率
    # today_rate = serializers.SerializerMethodField(read_only=True)
    #
    # def get_today_rate(self, obj):
    #     a = self.get_today_success_num(obj)
    #     b = self.get_today_total_num(obj)
    #     if b == 0 or a == 0:
    #         return '0%'
    #     return ('{:.2%}'.format(a / b))

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

    # 昨天 成功率
    # yesterday_rate = serializers.SerializerMethodField(read_only=True)
    #
    # def get_yesterday_rate(self, obj):
    #     a = self.get_yesterday_success_num(obj)
    #     b = self.get_yesterday_total_num(obj)
    #     if b == 0 or a == 0:
    #         return '0%'
    #     return ('{:.2%}'.format(a / b))

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

    # 当月 成功率
    # month_rate = serializers.SerializerMethodField(read_only=True)
    #
    # def get_month_rate(self, obj):
    #     a = self.get_month_success_num(obj)
    #     b = self.get_month_total_num(obj)
    #     if b == 0 or a == 0:
    #         return '0%'
    #     return ('{:.2%}'.format(a / b))

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
        fields = ['id', 'username', 'add_time', 'hour_total_num',
                  'hour_success_num', 'hour_money_all', 'hour_money_success', 'today_total_num',
                  'today_success_num', 'today_money_all', 'today_money_success', 'yesterday_total_num',
                  'yesterday_success_num', 'yesterday_money_all', 'yesterday_money_success',
                  'month_total_num',
                  'month_success_num', 'month_money_all', 'month_money_success']



class UserCODataSerializer(serializers.ModelSerializer):
    # add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    # username = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username']


class OrderGetSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    money = serializers.SerializerMethodField(read_only=True)
    def get_money(self, instance):

        return int(instance.total_amount)*100
    class Meta:
        model = OrderInfo
        fields = ['id','money']