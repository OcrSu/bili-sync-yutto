FROM python:3.12-alpine

WORKDIR /usr/src/app

COPY . .

RUN	apk add --no-cache git ffmpeg && \
ln -s /root /app && \
pip install --no-cache-dir -r git+https://github.com/Nemo2011/bilibili-api.git@dev && \
pip install git+https://github.com/yutto-dev/yutto@main
rm -rf /var/cache/apk/

CMD [ "python", "main.py" ]
