import datetime
import json
import re
from decimal import Decimal

import requests
from django.http import HttpResponse

from trade.models import OrderInfo
from user.models import UserProfile
from utils.common import JsonCustomEncoder


def callback():
    order_all=OrderInfo.objects.filter(pay_status=0,trade_no__isnull=False)
    if not order_all:
        return
    for order_obj in order_all:
        r = requests.get(
            'https://spay3.swiftpass.cn/spay/getCallbackUrl?mchId=' + order_obj.nsm.appid + '&userId=&outTradeNo=' + order_obj.out_trade_no)
        if r.status_code == 200:
            money_pattern = re.compile(r'<p id="money">(.*?)</p>')
            orderNoMch_pattern = re.compile(r'<p id="orderNoMch">(.*?)</p>')
            outTradeNo_pattern = re.compile(r'<p id="outTradeNo">(.*?)</p>')
            money = money_pattern.findall(r.text)
            orderNoMch = orderNoMch_pattern.findall(r.text)
            outTradeNo = outTradeNo_pattern.findall(r.text)
            if money[0] and outTradeNo[0] == order_obj.out_trade_no and orderNoMch[0]:
                # 修改商户金额
                User_obj = UserProfile.objects.get(id=order_obj.user_id)
                proxy_id = User_obj.proxy_id
                User_obj.total_money = '%.2f' % (Decimal(User_obj.total_money) + Decimal(order_obj.real_money))
                User_obj.money = '%.2f' % (Decimal(User_obj.money) + Decimal(order_obj.real_money) - Decimal(
                    order_obj.service_money))
                User_obj.save()
                # 修改代理金额
                Proxy_obj = UserProfile.objects.get(id=proxy_id)
                Proxy_obj.total_money = '%.2f' % (
                        Decimal(Proxy_obj.total_money) + Decimal(order_obj.real_money))
                Proxy_obj.money = '%.2f' % (Decimal(Proxy_obj.money) + Decimal(order_obj.real_money) - Decimal(
                    order_obj.service_money))
                Proxy_obj.save()
                # 修改admin金额
                admin_obj = UserProfile.objects.filter(is_superuser=1)[0]
                admin_obj.total_money = '%.2f' % (
                        Decimal(admin_obj.total_money) + Decimal(order_obj.real_money))
                admin_obj.money = '%.2f' % (Decimal(admin_obj.money) + Decimal(order_obj.real_money) - Decimal(
                    order_obj.service_money))
                admin_obj.save()

                # 修改农商收款
                order_obj.nsm.money = (order_obj.nsm.money + order_obj.order_money).quantize(Decimal('0.00'))
                if order_obj.nsm.is_limit:
                    order_obj.nsm.variable_money = (order_obj.nsm.variable_money - order_obj.order_money).quantize(
                        Decimal('0.00'))
                order_obj.nsm.save()

                # NsshInfo.objects.get(id=order_obj.nsm_id)
                # 回调用户
                # 修改订单状态
                postdata={}
                postdata['pay_time'] = str((datetime.datetime.now()).strftime(format('%Y-%m-%d %H:%M')))
                order_obj.pay_time = postdata['pay_time']
                headers = {'Content-Type': 'application/json'}
                data = json.dumps(postdata, cls=JsonCustomEncoder)
                try:
                    r = requests.post(order_obj.notify_url, data=data, headers=headers, timeout=10)
                    print(r.status_code)
                    if r.status_code == 200:
                        order_obj.pay_status = 1
                        order_obj.save()

                    else:
                        order_obj.pay_status = 3
                        order_obj.save()
                except Exception:
                    order_obj.pay_status = 3
                    order_obj.save()

                if order_obj.nsm.variable_money <= 0 and order_obj.nsm.is_limit:
                    order_obj.nsm.is_active = False
                    order_obj.nsm.save()

                # 日志记录
                print('订单号：'+order_obj.order_no,'金额：'+str(order_obj.order_money),'订单状态：'+str(order_obj.pay_status))
    return
