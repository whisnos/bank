import random
import re
import time
from decimal import Decimal

from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response

from bank.settings import FONT_DOMAIN
from channel.models import channelInfo
from proxy.models import ReceiveBankInfo, RateInfo
from trade.models import OrderInfo
from user.models import UserProfile
from utils.make_code import make_short_code


class MakePay(object):
    def __init__(self, user, order_money, real_money, channel, remark, order_id, decive_obj, notify_url):
        self.user = user
        self.order_money = order_money
        self.channel = channel
        self.real_money = real_money
        self.remark = remark
        self.order_id = order_id
        self.decive_obj = decive_obj
        self.notify_url = notify_url

    def choose_pay(self):
        resp = {}
        channel_queryset = channelInfo.objects.filter(channel_name=self.channel)
        if not channel_queryset:
            resp['msg'] = '通道未开通，无法创建订单'
            return resp
        channel_id = channel_queryset[0].id

        R_queryset = RateInfo.objects.filter(user_id=self.user.id, is_active=True, is_map=True,
                                             channel_id=channel_id)
        if R_queryset:
            mapid = R_queryset[0].mapid
            new_queryset = RateInfo.objects.filter(id=mapid)
            channel_id = new_queryset[0].channel_id
            thirt_queryset = RateInfo.objects.filter(user_id=self.user.id, is_active=True, channel_id=channel_id)
            if not thirt_queryset:
                resp['msg'] = '通道未开通，无法创建订单'
                return resp
            self.channel=channel_id
            rate=thirt_queryset[0].rate
        else:
            RR_queryset = RateInfo.objects.filter(user_id=self.user.id, is_active=True, channel_id=channel_id)
            print('RR_queryset',RR_queryset)
            if not RR_queryset and len(R_queryset) != 1:
                resp['msg'] = '找不到对应费率'
                code = 404
                return Response(data=resp, status=code)
            else:
                channel_id = RR_queryset[0].channel_id
                self.channel = channel_id
                print('self.channel',self.channel)
                rate = RR_queryset[0].rate
        if self.channel == 1: # atb

            # rateinfo_queryset=RateInfo.objects.filter(user_id=self.user.id,is_active=True,)
            # if not rateinfo_queryset:
            #     resp['msg'] = '通道未开通，无法创建订单'
            #     return resp

            bank_queryet = ReceiveBankInfo.objects.filter(is_active=True, user_id=self.user.proxy_id,device=self.decive_obj.id)
            if not bank_queryet:
                resp['msg'] = '收款商户未激活,或不存在有效收款卡'
                return resp

            short_code = make_short_code(8)
            order_no = "{time_str}{userid}{randstr}".format(time_str=time.strftime("%Y%m%d%H%M%S"),
                                                            userid=self.user.id, randstr=short_code)
            # # # 处理金额
            # while True:
            #     for bank in bank_queryet:
            #         order_queryset = OrderInfo.objects.filter(pay_status=0, order_money=self.real_money,
            #                                                   account_num=bank.card_number)
            #         if not order_queryset:
            #             account_num = bank.card_number
            #             break
            #         else:
            #             continue
            #     if order_queryset:
            #         self.real_money = (Decimal(self.real_money) + Decimal(random.uniform(-0.9, 0.9))).quantize(
            #             Decimal('0.00'))
            #     else:
            #         break
            while True:
                order_queryset=OrderInfo.objects.filter(pay_status=0, real_money=self.real_money,device=self.decive_obj.id)
                if order_queryset:
                    self.real_money = (Decimal(self.real_money) + Decimal(0.01)).quantize(Decimal('0.00'))
                else:
                    break
            service_money = (Decimal(self.real_money)*Decimal(rate)).quantize(Decimal('0.00'))
            print('service_money',service_money)
            # 随机ch抽一张银行卡
            account_num=random.choice(bank_queryet).card_number
            print('account_num',account_num)
            order = OrderInfo()
            order.user_id = self.user.id
            order.channel_id = channel_id
            order.device_id = self.decive_obj.id
            order.proxy = self.user.proxy_id
            order.order_no = order_no
            order.pay_status = 0
            order.order_money = self.order_money
            order.real_money = self.real_money
            order.remark = self.remark
            order.order_id = self.order_id
            order.account_num = account_num
            order.notify_url=self.notify_url
            order.service_money=service_money
            pay_url = FONT_DOMAIN + '/pay/' + order_no
            order.pay_url = pay_url
            order.save()
            resp['order_no'] = order_no
            resp['pay_url'] = pay_url
            resp['id'] = order.id
            resp['msg'] = '创建成功'
            resp['code'] = 200
            resp['order_money'] = self.order_money
            resp['real_money'] = self.real_money
            resp['order_id'] = self.order_id
            resp['add_time'] = str(order.add_time)
            resp['channel'] = 'atb'
            return resp
        elif self.channel == 2:
            order = OrderInfo()
            order.user_id = self.user.id
            order.channel_id = 2
            # order.device_id = self.decive_obj.id
            # order.order_no = order_no
            order.pay_status = 0
            order.real_money = self.real_money
            order.order_money = self.order_money
            order.remark = self.remark
            order.order_id = self.order_id
            order.receive_way = '0'
            order.notify_url = self.notify_url
            order.proxy = self.user.proxy_id
            order.save()
            resp['msg'] = '创建成功'
            resp['code'] = 200
            resp['order_money'] = self.order_money
            # resp['real_money'] = self.real_money
            resp['order_id'] = self.order_id
            resp['add_time'] = str(order.add_time)
            resp['channel'] = 'wang'
            return resp
        elif self.channel == 3:
            resp['code'] = 404
            resp['msg'] = 'alipay通道暂未开通'
            return resp
        else:
            resp['code'] = 404
            resp['msg'] = '通道不存在'
            return resp
