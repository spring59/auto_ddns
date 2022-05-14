# auto_ddns 
仅支持CloudFlare，因之前使用别人的开源软件，总是会有未知的ip访问服务，所以写了这个小脚本
自动解析家庭动态公网IP到**CloudFlare**

Automatically resolve the family dynamic public IP to CloudFlare

从这三个网站获取公网ip

1.https://ip.3322.net

2.https://ddns.oray.com/checkip

3.https://myip.ipip.net/

Server酱：
微信通知服务
https://sct.ftqq.com/
# 运行脚本
git clone git@github.com:spring59/auto_ddns.git

cd auto_ddns

配置config.ini相关参数

pip3 install -r requirements.txt

方法一：脚本后加& 加了&以后可以使脚本在后台运行，这样的话你就可以继续工作了。但是有一个问题就是你关闭终端连接后，脚本会停止运行

python3  main.py >/dev/null 2>&1 &

方法二：使用nohup在后台执行命令 关闭终端不会停止脚本

nohup python3  main.py >/dev/null 2>&1 &

# DOCKER 启动方式
# 一.

 docker search spring59/auto_ddns

linux/arm:

 docker pull spring59/auto_ddns:1.0

linux/amd64:

 docker pull spring59/auto_ddns:latest

通过传参的方式启动 无需修改config.ini

docker run -d --name auto_ddns  --restart=always -e token="*****" -e  host="*****" -e j="*****" -e sleep="10" auto_ddns 

# 二.
git clone git@github.com:spring59/auto_ddns.git

cd auto_ddns && 配置config.ini相关参数

docker build -t {repo_name} .

docker run -d --name auto_ddns  --restart=always  {repo_name}/auto_ddns


# 参数说明：
token: cloudflare的token,必传

host: 一级或者二级 web url,公网要绑定的网址,必传

j: server酱token,没有则不通知微信,非必传

sleep: 每次检测时间间隔,非必传（单位/分钟）