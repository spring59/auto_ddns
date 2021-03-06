FROM python:3.7-alpine
COPY requirements.txt /requirements.txt
# 安装支持 删除缓存文件和虚拟包
RUN apk --no-cache add --virtual .build-deps \
    build-base \
    && pip install -r /requirements.txt \
    && rm -rf .cache/pip \
    && apk del .build-deps \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' >/etc/timezon

ENV app /app
WORKDIR ${app}
ADD config.ini config.py main.py /$app
ENV token = ''
ENV host = ''
ENV j = ''
ENV sleep = ''
ENTRYPOINT python3 main.py --token=$token --host=$host --j=$j --sleep=$sleep
