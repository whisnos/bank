import random
import re
import time
from decimal import Decimal

from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response

from bank.settings import FONT_DOMAIN, APP_NOTIFY_URL, ALIPAY_DEBUG, REDIRECT_URL
from channel.models import channelInfo, AlipayInfo
from proxy.models import ReceiveBankInfo, RateInfo, DeviceInfo
from trade.models import OrderInfo
from user.models import UserProfile
from utils.alipay import AliPay
from utils.make_code import make_short_code
from utils.permissions import MakeLogs


class MakePay(object):
    def __init__(self, user, order_money, real_money, channel, remark, order_id, notify_url, plat_type, return_url):
        self.user = user
        self.order_money = order_money
        self.channel = channel
        self.real_money = real_money
        self.remark = remark
        self.order_id = order_id
        self.notify_url = notify_url
        self.plat_type = plat_type
        self.return_url = return_url

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
            self.channel = channel_id
            ci_obj = channelInfo.objects.filter(id=channel_id)[0]
            name = ci_obj.channel_name
            rate = thirt_queryset[0].rate
        else:
            RR_queryset = RateInfo.objects.filter(user_id=self.user.id, is_active=True, channel_id=channel_id)
            print('RR_queryset', RR_queryset)
            if not RR_queryset and len(R_queryset) != 1:
                resp['msg'] = '找不到对应费率'
                resp['code'] = 404
                return resp
            else:
                channel_id = RR_queryset[0].channel_id
                self.channel = channel_id
                ci_obj = channelInfo.objects.filter(id=channel_id)[0]
                name = ci_obj.channel_name
                print('self.channel', self.channel)
                rate = RR_queryset[0].rate
        if name == 'atb':  # atb
            device_queryset = DeviceInfo.objects.filter(user_id=self.user.proxy_id, is_active=True)
            if not device_queryset:
                resp['code'] = 404
                resp['msg'] = '设备未激活,或不存在有效设备'
                return Response(resp)
            decive_obj = random.choice(device_queryset)

            bank_queryet = ReceiveBankInfo.objects.filter(is_active=True, user_id=self.user.proxy_id,
                                                          device=decive_obj.id)
            if not bank_queryet:
                resp['msg'] = '收款商户未激活,或不存在有效收款卡'
                return resp
            short_code = make_short_code(8)
            order_no = "{time_str}{userid}{randstr}".format(time_str=time.strftime("%Y%m%d%H%M%S"),
                                                            userid=self.user.id, randstr=short_code)
            while True:
                order_queryset = OrderInfo.objects.filter(pay_status=0, real_money=self.real_money,
                                                          device=decive_obj.id)
                if order_queryset:
                    self.real_money = (Decimal(self.real_money) + Decimal(0.01)).quantize(Decimal('0.00'))
                else:
                    break
            service_money = (Decimal(self.real_money) * Decimal(rate)).quantize(Decimal('0.00'))

            # 随机ch抽一张银行卡
            account_num = random.choice(bank_queryet).card_number
            order = OrderInfo()
            order.user_id = self.user.id
            order.channel_id = channel_id
            order.device_id = decive_obj.id
            order.proxy = self.user.proxy_id
            order.order_no = order_no
            order.pay_status = 0
            order.order_money = self.order_money
            order.real_money = self.real_money
            order.remark = self.remark
            order.order_id = self.order_id
            order.account_num = account_num
            order.notify_url = self.notify_url
            order.service_money = service_money
            pay_url = FONT_DOMAIN + '/pay/' + order_no
            order.pay_url = pay_url
            order.save()
            # 引入日志
            log = MakeLogs()
            content = '用户：' + str(self.user.username) + ' 创建订单号：' + str(order_no) + ' 金额：' + str(
                self.order_money) + ' 元' + '-' + 'atb'
            log.add_logs(1, content, self.user.id)
            resp['msg'] = '创建成功'
            resp['order_no'] = order_no
            resp['pay_url'] = pay_url
            resp['remark'] = self.remark
            resp['id'] = order.id
            resp['code'] = 200
            resp['order_money'] = Decimal(self.order_money)
            resp['real_money'] = Decimal(self.real_money)
            resp['order_id'] = self.order_id
            resp['add_time'] = str(order.add_time.strftime(format("%Y-%m-%d %H:%M")))
            resp['channel'] = 'atb'
            return resp
        elif name == 'wang':
            order = OrderInfo()
            order.user_id = self.user.id
            order.channel_id = channel_id
            order.pay_status = 0
            order.real_money = self.real_money
            order.order_money = self.order_money
            order.remark = self.remark
            order.order_id = self.order_id
            order.notify_url = self.notify_url
            order.proxy = self.user.proxy_id
            order.save()
            resp['msg'] = '创建成功'
            resp['code'] = 200
            resp['order_money'] = self.order_money
            resp['order_id'] = self.order_id
            resp['add_time'] = str(order.add_time.strftime(format("%Y-%m-%d %H:%M")))
            resp['channel'] = 'wang'
            return resp
        elif name == 'alipay':
            c_queryet = AlipayInfo.objects.filter(is_active=True, user_id=self.user.proxy_id).all()
            if not c_queryet:
                resp['code'] = 404
                resp['msg'] = '收款商户未激活'
                return resp
            short_code = make_short_code(8)
            order_no = "{time_str}{userid}{randstr}".format(time_str=time.strftime("%Y%m%d%H%M%S"),
                                                            userid=self.user.id, randstr=short_code)
            receive_c = random.choice(c_queryet)
            app_id = receive_c.c_appid
            private_key_path = receive_c.c_private_key
            ali_public_path = receive_c.alipay_public_key
            alipay = AliPay(
                appid=app_id,
                app_notify_url=APP_NOTIFY_URL,
                app_private_key_path=private_key_path,  # 个人私钥
                alipay_public_key_path=ali_public_path,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
                debug=ALIPAY_DEBUG,  # 默认False,
                return_url=self.return_url,
                plat_type=str(self.plat_type),
            )

            url = alipay.direct_pay(
                subject=order_no,
                out_trade_no=order_no,
                total_amount=self.order_money
            )
            # if str(self.plat_type) == '1':
            #     resp['re_url'] = REDIRECT_URL + url
            #     url = resp['re_url']
            # else:
            resp['re_url'] = url
            order = OrderInfo()
            order.user_id = self.user.id
            order.channel_id = channel_id
            order.pay_status = 0
            order.real_money = self.real_money
            order.order_money = self.order_money
            order.remark = self.remark
            order.order_id = self.order_id
            order.order_no = order_no
            order.notify_url = self.notify_url
            order.proxy = self.user.proxy_id
            order.pay_url = url
            order.save()
            resp['msg'] = '创建成功'
            resp['code'] = 200
            resp['order_money'] = self.order_money
            resp['order_id'] = self.order_id
            resp['add_time'] = str(order.add_time.strftime(format("%Y-%m-%d %H:%M")))
            resp['channel'] = 'alipay'
            return resp
        else:
            resp['code'] = 404
            resp['msg'] = '通道不存在'
            return resp
