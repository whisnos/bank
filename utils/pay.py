import re

from rest_framework.response import Response

from user.models import UserProfile


class MakePay(object):
    def __init__(self, uid, real_money, order_id, return_url, channel, key,user_queryset):
        self.uid = uid
        self.real_money = real_money
        self.order_id = order_id
        self.return_url = return_url
        self.channel = channel
        self.key = key
        self.user_queryset=user_queryset
    def check_sta(self):
        resp = {}
        if not str(self.real_money) > '1':
            resp['msg'] = '金额必须大于1'
            return Response(resp, status=404)
        if not self.order_id:
            resp['msg'] = '请填写订单号~~'
            return Response(resp, status=404)
        if not self.return_url:
            resp['msg'] = '请填写正确跳转url~~'
            return Response(resp, status=404)
        if not self.user_queryset:
            resp['msg'] = 'uid或者auth_code错误，请重试~~'
            return Response(resp, status=404)
        if not re.match(r'(^[1-9]([0-9]{1,4})?(\.[0-9]{1,2})?$)|(^(0){1}$)|(^[0-9]\.[0-9]([0-9])?$)',
                        str(self.real_money)):
            resp['msg'] = '金额输入错误，请重试~~0.01到5万间'
            return Response(resp, status=404)
