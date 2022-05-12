# This is a sample Python script.
import json
import sys
import os
import logging, logging.handlers
import time
import requests
import re
from config import global_config

TOKEN_CLOUD = global_config.get("config", "CLOUD_FLARE_TOKEN")
DNS_ADDRESS = global_config.get("config", "DNS_ADDRESS")
FANG_TANG_TOKEN = global_config.get("config", "FANG_TANG_TOKEN")
ZERO_ID = ''
SLEEP_TIME = int(global_config.get("config", "SLEEP_TIME")) * 60
try_num = int(global_config.get("config", "TRY_NUM"))
# 通知微信方糖服务号
WX_API_HOST = 'https://sctapi.ftqq.com/' + FANG_TANG_TOKEN + '.send?title={0}&desp={1}'

# 第一种日志方式
# LOG_FORMAT = '[%(levelname)s] %(asctime)s - %(message)s'
# logging.basicConfig(
#     level=logging.INFO,
#     format=LOG_FORMAT,
#     handlers=[
#         #logging.FileHandler("dns.log"),
#         logging.StreamHandler(sys.stdout)
#     ],
#     datefmt="%Y-%m-%d %H:%I:%S"
# )
# 第二种日志方式
if os.path.exists('log'):
    pass
else:
    os.mkdir('log')
LOG_FORMAT = "[%(levelname)s]%(asctime)s - %(message)s"
date_fmt = "%Y-%m-%d %H:%M:%S"
f_name = time.strftime("_%Y%m%d.log", time.localtime())
level = logging.INFO
# 创建TimedRotatingFileHandler对象,每天生成一个文件
log_file_handler = logging.handlers.TimedRotatingFileHandler(filename='log/dns.log', when="midnight", interval=1
                                                             , backupCount=3, encoding='utf-8')
log_file_handler.suffix = f_name
# 设置日志打印格式
log_file_handler.setLevel(level)
formatter = logging.Formatter(LOG_FORMAT, datefmt=date_fmt)
log_file_handler.setFormatter(formatter)
logging.basicConfig(level=level, format=LOG_FORMAT, datefmt=date_fmt)
logging.getLogger('').addHandler(log_file_handler)


def wx_ft_notice(currentIp, updateRes, hostName):
    title = '主人IPv4变了:%s,hk1更改结果:%s' % (currentIp, "成功" if updateRes else "失败")
    desp = hostName;
    url = WX_API_HOST.format(title, desp)
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
    except:
        logging.info("请求服务商url失败")
    return None


def get_cloudflare_zero_id():
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
                return domains['id']
    except Exception as e:
        logging.info("获取区域id失败" + e)
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


ZERO_ID = get_cloudflare_zero_id()
# 开始程序
if __name__ == '__main__':
    if ZERO_ID is not '':
        logging.info('加载区域id成功')
    else:
        logging.info('加载区域id失败')
        sys.exit(0)
    loopMonitor()
