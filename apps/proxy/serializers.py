from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from proxy.models import RateInfo
from user.models import UserProfile


class ProxyUserDetailSerializer(serializers.ModelSerializer):
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
