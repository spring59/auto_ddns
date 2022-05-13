FROM python:3.7-alpine

COPY requirements.txt /requirements.txt
# 安装支持 删除缓存文件和虚拟包
RUN apk --no-cache add --virtual .build-deps \
    build-base \
    && pip install -r /requirements.txt \
    && rm -rf .cache/pip \
    && apk del .build-deps \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' >/etc/timezon


RUN mkdir app
ENV app /app
WORKDIR ${app}
ADD config.ini config.py main.py /$app
#当容器启动时，使用python3执行指定路径的py脚本
#CMD ["python3", " main.py --token $token --host $host --j $j --sleep $sleep"]cmd
ENV token = ''
ENV host = ''
ENV j = ''
ENV sleep = ''
ENTRYPOINT python3 main.py --token=$token --host=$host --j=$j --sleep=$sleep
#ENTRYPOINT ["python3","main.py --token=$token --host=$host --j=$j --sleep=$sleep"]
