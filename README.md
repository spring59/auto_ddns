# auto_ddns 
仅支持CloudFlare，因之前使用别人的开源软件，总是会有未知的ip访问主机，所以写了这个小脚本
自动解析家庭动态公网IP到**CloudFlare**

Automatically resolve the family dynamic public IP to CloudFlare

Server酱：
微信通知服务
https://sct.ftqq.com/
# 运行脚本
git clone git@github.com:spring59/auto_ddns.git

cd auto_ddns

pip3 install -r requirements.txt

方法一：脚本后加& 加了&以后可以使脚本在后台运行，这样的话你就可以继续工作了。但是有一个问题就是你关闭终端连接后，脚本会停止运行

python3  main.py >/dev/null 2>&1 &

方法二：使用nohup在后台执行命令 关闭终端不会停止脚本

nohup python3  main.py >/dev/null 2>&1 &
