FROM python:3.12-alpine

WORKDIR /usr/src/app

COPY . .

# 合并多个RUN命令到一个，并清理安装时产生的缓存
RUN	apk add --no-cache git ffmpeg && \
ln -s /root /app && \
pip install --no-cache-dir -r requirements.txt && \
pip install git+https://github.com/OcrSu/yutto@main && \
rm -rf /var/cache/apk/

CMD [ "python", "bili-sync-yutto.py" ]
