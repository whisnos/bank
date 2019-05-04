import random
from decimal import Decimal
from Cryptodome.PublicKey import RSA
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect

from Cryptodome.Signature import PKCS1_v1_5
from Cryptodome.Hash import SHA256
from base64 import encodebytes
from urllib.parse import quote_plus
import time
import requests
from bank.settings import BASE_DIR
import datetime
from utils.make_code import make_md5
from bank.settings import DEFAULT_RATE, CLOSE_TIME, SECRET_VERIFY
from trade.models import OrderInfo
from bank.settings import FONT_DOMAIN
from user.models import UserProfile
from nsm.models import NsshInfo
import json
import re
from utils.common import JsonCustomEncoder


# 查询订单
def nsm_query(request):
    order_id = request.GET.get('id')
    print('order_id', order_id)
    resp = {}
    if order_id:

        # 关闭超时订单
        now_time = datetime.datetime.now() - datetime.timedelta(minutes=CLOSE_TIME)
        OrderInfo.objects.filter(pay_status=0, add_time__lte=now_time).update(
            pay_status=2)

        order_queryset = OrderInfo.objects.filter(pay_status=0, order_no=order_id)
        print(order_queryset)
        if order_queryset:
            order_obj = order_queryset[0]
            resp['id'] = order_obj.id
            resp['order_no'] = order_obj.order_no
            resp['pay_status'] = order_obj.pay_status
            resp['add_time'] = order_obj.add_time
            resp['real_money'] = order_obj.real_money
            resp['trade_no'] = order_obj.trade_no
            resp['out_trade_no'] = order_obj.out_trade_no
            resp['remark'] = order_obj.remark
            return JsonResponse(data=resp, status=200)
        else:
            resp['msg'] = '订单不存在'
            return JsonResponse(data=resp, status=400)

    else:
        resp['msg'] = '订单不存在'
        return JsonResponse(data=resp, status=400)


# 获取userid 创建支付宝订单
def get_ali_userid(request):
    resp = {}
    appid = request.GET.get('app_id', None)
    auth_code = request.GET.get('auth_code', None)
    state = request.GET.get('state', None)
    url = 'https://openapi.alipay.com/gateway.do?'
    if state and auth_code and appid:
        order_queryset = OrderInfo.objects.filter(pay_status=0, order_no=state, trade_no=None)
        if order_queryset:
            order_obj = order_queryset[0]
            c_queryet = NsshInfo.objects.filter(user_id=order_obj.proxy,is_active=True)
            if not c_queryet:
                return JsonResponse(data={"msg": "没有绑定收款商户"}, status=400)
            payload = {
                "app_id": appid,
                "method": "alipay.system.oauth.token",
                "format": "json",
                "charset": "utf-8",
                "sign_type": "RSA2",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "version": "1.0",
                "grant_type": "authorization_code",
                "code": auth_code
            }

            with open(BASE_DIR + '/utils/key.pem') as f:
                private_key = f.read()
            orderstr = sign_data(payload, private_key)
            url = url + orderstr
            try:
                r = requests.get(url)
                response = r.json()
                userid = response['alipay_system_oauth_token_response']['user_id']
            except Exception:
                return JsonResponse(data={"msg": "订单创建失败"}, status=400)
            c_queryet_turn = c_queryet.filter(is_turn=False)

            if not c_queryet_turn:
                c_queryet.update(is_turn=False)
                receive_c=c_queryet[0]
            else:
                receive_c = c_queryet_turn[0]
            receive_c.is_turn = True
            receive_c.save()
            postdata = {
                # 113570009362
                "mchId": receive_c.appid,
                "mchName": receive_c.mch_name,
                "body": order_obj.order_no,
                "buyerId": userid,
                "money": str(int(order_obj.real_money * 100))
            }
            headers = {
                'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16A366 NebulaSDK/1.8.100112 Nebula WK PSDType(1) AlipayDefined(nt:WIFI,ws:375|603|2.0) AliApp(AP/10.1.60.6001) AlipayClient/10.1.60.6001 Alipay Language/zh-Hans',
                'Content-type': 'application/x-www-form-urlencoded'
            }
            try:
                res = requests.post('https://spay3.swiftpass.cn/spay/fixedCodePayV2', data=postdata, headers=headers)
                res_json = res.json()
                if res_json['status'] == "200":
                    order_obj.out_trade_no = res_json['message']['outTradeNo']
                    order_obj.trade_no = res_json['message']['tradeNO']
                    order_obj.nsm = receive_c
                    order_obj.save()
                    return HttpResponseRedirect(FONT_DOMAIN + '/tradepay/' + state)
            except Exception:
                return JsonResponse(data={"msg": "订单创建失败"}, status=400)

    return JsonResponse(data={"msg": "订单创建失败"}, status=400)


# 农商回调
def nsmbackcall(request):
    order_no = request.GET.get('order_no', None)
    if order_no:
        order_queryset = OrderInfo.objects.filter(pay_status=0, order_no=order_no, trade_no__isnull=False)
        if order_queryset:
            postdata = {}
            order_obj = order_queryset[0]
            mchid = order_obj.nsm.appid
            notify = order_obj.notify_url
            postdata['msg'] = '订单处理成功!'
            postdata['pay_status'] = 1
            postdata['add_time'] = str(order_obj.add_time)
            postdata['order_money'] = order_obj.order_money
            postdata['real_money'] = order_obj.real_money
            postdata['order_id'] = order_obj.order_id
            postdata['order_no'] = order_obj.order_no
            postdata['channel'] = order_obj.channel.channel_name
            postdata['remark'] = order_obj.remark
            print('postdata',postdata)
            key = str(order_obj.user.uid + order_obj.order_no + str(order_obj.order_money) + order_obj.user.auth_code)
            postdata['key'] = make_md5(key)

            try:
                r = requests.get(
                    'https://spay3.swiftpass.cn/spay/getCallbackUrl?mchId=' + order_obj.nsm.appid + '&userId=&outTradeNo=' + order_obj.out_trade_no)
                if r.status_code == 200:
                    money_pattern = re.compile(r'<p id="money">(.*?)</p>')
                    orderNoMch_pattern = re.compile(r'<p id="orderNoMch">(.*?)</p>')
                    outTradeNo_pattern = re.compile(r'<p id="outTradeNo">(.*?)</p>')
                    money = money_pattern.findall(r.text)
                    orderNoMch = orderNoMch_pattern.findall(r.text)
                    outTradeNo = outTradeNo_pattern.findall(r.text)
                    print('农商回调', money, orderNoMch, outTradeNo)
                    if money[0] and outTradeNo[0] == order_obj.out_trade_no and orderNoMch[0]:
                        print('8888')
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
                            order_obj.nsm.variable_money = (order_obj.nsm.variable_money - order_obj.order_money).quantize(Decimal('0.00'))
                        order_obj.nsm.save()

                        # NsshInfo.objects.get(id=order_obj.nsm_id)
                        # 回调用户
                        # 修改订单状态
                        postdata['pay_time'] = str((datetime.datetime.now()).strftime(format('%Y-%m-%d %H:%M')))
                        order_obj.pay_time = postdata['pay_time']
                        headers = {'Content-Type': 'application/json'}
                        data = json.dumps(postdata, cls=JsonCustomEncoder)
                        print('notify',data)
                        try:
                            r = requests.post(notify, data=data, headers=headers, timeout=10)
                            print(888,dir(r))
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

                        if order_obj.nsm.variable_money<=0 and order_obj.nsm.is_limit:
                            order_obj.nsm.is_active =False
                            order_obj.nsm.save()
                        return HttpResponse('ok')
            except Exception:
                return JsonResponse(data={"msg": "验证失败"}, status=400)
    return JsonResponse(data={"msg": "验证失败"}, status=400)


# 对payload数据进行排序和拼接
def ordered_data(data):
    import json
    complex_keys = []
    for key, value in data.items():
        if isinstance(value, dict):
            complex_keys.append(key)

    # 将字典类型的数据dump出来
    for key in complex_keys:
        data[key] = json.dumps(data[key], separators=(',', ':'))

    return sorted([(k, v) for k, v in data.items()])


def sign(unsigned_string, private_key=None):
    # 开始计算签名
    key = private_key
    rsakey = RSA.importKey(key)

    signer = PKCS1_v1_5.new(rsakey)

    signature = signer.sign(SHA256.new(unsigned_string))
    # base64 编码，转换为unicode表示并移除回车
    sign = encodebytes(signature).decode("utf8").replace("\n", "")
    return sign


def sign_data(data, key):
    data.pop("sign", None)
    # 排序后的字符串
    unsigned_items = ordered_data(data)
    unsigned_string = "&".join("{0}={1}".format(k, v) for k, v in unsigned_items)
    signstr = sign(unsigned_string.encode("utf-8"), key)

    # ordered_items = self.ordered_data(data)
    quoted_string = "&".join("{0}={1}".format(k, quote_plus(v)) for k, v in unsigned_items)

    # 获得最终的订单信息字符串
    signed_string = quoted_string + "&sign=" + quote_plus(signstr)
    return signed_string
def make_hw():
    print('hello world')