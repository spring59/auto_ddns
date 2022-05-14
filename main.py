import json
import sys
import os
import logging, logging.handlers
import time
import requests
import re
import argparse
from config import global_config

TOKEN_CLOUD = ''
DNS_ADDRESS = ''
FANG_TANG_TOKEN = ''
ZERO_ID = ''
SLEEP_TIME = 10
try_num = 10
# 通知微信方糖服务号
WX_API_HOST = 'https://sctapi.ftqq.com/' + FANG_TANG_TOKEN + '.send?title={0}&desp={1}'
if os.path.exists('log'):
    pass
else:
    os.mkdir('log')
LOG_FORMAT = "[%(levelname)s]%(asctime)s - %(message)s"
date_fmt = "%Y-%m-%d %H:%M:%S"
f_name = time.strftime("_%Y%m%d.log", time.localtime())
level = logging.INFO
log_file_handler = logging.handlers.TimedRotatingFileHandler(filename='log/dns.log', when="midnight", interval=1
                                                             , backupCount=3, encoding='utf-8')
log_file_handler.suffix = f_name
log_file_handler.setLevel(level)
formatter = logging.Formatter(LOG_FORMAT, datefmt=date_fmt)
log_file_handler.setFormatter(formatter)
logging.basicConfig(level=level, format=LOG_FORMAT, datefmt=date_fmt)
logging.getLogger('').addHandler(log_file_handler)


def wx_ft_notice(currentIp, updateRes, hostName):
    if FANG_TANG_TOKEN is None or FANG_TANG_TOKEN == '':
        logging.info('未配置server酱token')
        return
    title = '主人IPv4变了:%s,hk1更改结果:%s' % (currentIp, "成功" if updateRes else "失败")
    description = hostName
    url = WX_API_HOST.format(title, description)
    response = requests.get(url)
    if response.status_code != 200:
        logging.info("wx 推送失败")
    else:
        logging.info('wx 推送成功')


def get_record_id(dns_name, zone_id, token):
    try:
        resp = requests.get(
            'https://api.cloudflare.com/client/v4/zones/{}/dns_records'.format(zone_id),
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            })
        if not json.loads(resp.text)['success']:
            return None
        domains = json.loads(resp.text)['result']
        for domain in domains:
            if dns_name == domain['name']:
                return domain['id'], domain['name'], domain['content']
    except Exception as e:
        logging.info("请求服务商url失败" + e)
    return None


def parse_cloudflare_zero_id():
    global ZERO_ID
    try:
        host_url = ''
        if DNS_ADDRESS.count('.') == 2:
            host_url = DNS_ADDRESS[DNS_ADDRESS.index('.') + 1:len(DNS_ADDRESS)]
        else:
            host_url = DNS_ADDRESS
        url = 'https://api.cloudflare.com/client/v4/zones?name={}&status=active' \
              '&page=1&per_page=20&order=status&direction=desc&match=all'.format(host_url)
        resp = requests.get(url,
                            headers={
                                'Authorization': 'Bearer ' + TOKEN_CLOUD,
                                'Content-Type': 'application/json'
                            })
        if json.loads(resp.text)['success']:
            domains = json.loads(resp.text)['result'][0]
            if domains is not None:
                ZERO_ID = domains['id']
                return ZERO_ID
        else:
            return None
    except Exception as e:
        logging.info("获取区域id失败 %s" % e)
    return None


def update_cloudflare_dns_record(dns_name, zone_id, token, dns_id, ip, proxied=False):
    try:
        resp = requests.put(
            'https://api.cloudflare.com/client/v4/zones/{}/dns_records/{}'.format(
                zone_id, dns_id),
            json={
                'type': 'A',
                'name': dns_name,
                'content': ip,
                'proxied': proxied
            },
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            })
        if not json.loads(resp.text)['success']:
            return False
    except:
        logging.info("请求服务商更新url失败")
        return False
    return True


reg = "(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"


def get_current_ip():
    # first get current public internet ip
    try:
        resp = requests.get("https://ip.3322.net")
        if resp.status_code == 200:
            return resp.text.replace('\n', '')
    except Exception as e:
        logging.info("3322获取当前公网失败！%s" % e)
    # second get current public internet ip
    try:
        resp = requests.get("https://ddns.oray.com/checkip")
        if resp.status_code == 200:
            return re.findall(reg, resp.text)[0]
    except Exception as e:
        logging.info("ora_y获取当前公网失败！%s" % e)
    try:
        resp = requests.get("https://myip.ipip.net/")
        if resp.status_code == 200:
            result = re.findall(reg, resp.text)
            return result[0]
    except Exception as e:
        logging.info("myip获取当前公网失败！%s" % e)
    time.sleep(SLEEP_TIME)
    return get_current_ip()


def compare_with_dns_server(concurrent_ip):
    obj = get_record_id(DNS_ADDRESS, ZERO_ID, TOKEN_CLOUD)
    if obj is None:
        return
    # print(strObj[0], strObj[1], strObj[2])
    if obj[2] == concurrent_ip:
        logging.info("你的IP:%s 没有变化, 域名:%s" % (concurrent_ip, DNS_ADDRESS))
    elif obj[2] != concurrent_ip:
        res = update_cloudflare_dns_record(DNS_ADDRESS, ZERO_ID, TOKEN_CLOUD, obj[0], concurrent_ip, False)
        if res:
            logging.info("您的域名发生了改变：当前域名：%s" % concurrent_ip)
            wx_ft_notice(concurrent_ip, res, obj[1])
        else:
            logging.info("您的域名更改失败！")


def loopMonitor():
    # 缓存ip
    temp_ip = ''
    str_template = 'IPv4未改变，将等待 {0} 次后与DNS服务商进行比对'
    num = try_num
    while True:
        ip = get_current_ip()
        if temp_ip == '':
            compare_with_dns_server(ip)
            temp_ip = ip
        elif num > 0:
            if temp_ip == ip:
                logging.info(str_template.format(num))
                num = num - 1
            else:
                compare_with_dns_server(ip)
                temp_ip = ip
                num = try_num
        else:
            compare_with_dns_server(ip)
            temp_ip = ip
            num = try_num
        time.sleep(SLEEP_TIME)


def is_not_empty(obj):
    if obj != '' and obj is not None:
        return True
    return False


# 初始化的参数
def init_params():
    global TOKEN_CLOUD
    global DNS_ADDRESS
    global FANG_TANG_TOKEN
    global SLEEP_TIME
    global try_num
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument('--token', type=str, default=None)
    parser.add_argument('--host', type=str, default=None)
    parser.add_argument('--j', type=str, default=None)
    parser.add_argument('--sleep', type=str, default=None)
    args = parser.parse_args()
    if is_not_empty(args.token) and is_not_empty(args.host):
        TOKEN_CLOUD = args.token
        DNS_ADDRESS = args.host
        global_config.set_section('config')
        global_config.set('config', 'cloud_flare_token', TOKEN_CLOUD)
        global_config.set('config', 'try_num', '10')
        global_config.set('config', 'dns_address', DNS_ADDRESS)
        if is_not_empty(args.j):
            FANG_TANG_TOKEN = args.j
            global_config.set('config', 'fang_tang_token', FANG_TANG_TOKEN)
        if is_not_empty(args.sleep):
            SLEEP_TIME = int(args.sleep) * 60
            global_config.set('config', 'sleep_time', args.sleep)
        global_config.writer_all()
        logging.info("初始化参数成功")
    else:
        TOKEN_CLOUD = global_config.get("config", "cloud_flare_token")
        DNS_ADDRESS = global_config.get("config", "dns_address")
        FANG_TANG_TOKEN = global_config.get("config", "fang_tang_token")
        SLEEP_TIME = int(global_config.get("config", "sleep_time")) * 60
        try_num = int(global_config.get("config", "try_num"))
        logging.info("加载参数成功")


# 开始程序
if __name__ == '__main__':
    init_params()
    parse_cloudflare_zero_id()
    if len(ZERO_ID) != 0:
        logging.info('加载区域id成功')
    else:
        logging.info('加载区域id失败')
        sys.exit(0)
    loopMonitor()
