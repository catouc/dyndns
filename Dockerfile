FROM python:3.7.4-alpine3.10 

LABEL maintainer="boeschenphilip@gmail.com"
LABEL version="0.1.1"

COPY src .

# https://stackoverflow.com/questions/52894632/cannot-install-pycosat-on-alpine-during-dockerizing
RUN mkdir -p /usr/include/sys && \
      echo "#include <unistd.h>" > /usr/include/sys/unistd.h && \
      apk add --update-cache make && \
      apk add --virtual .build-deps gcc \
                                    musl-dev \
                                    linux-headers \
                                    libffi-dev \
                                    openssl-dev && \
      pip install -r requirements.txt

CMD ["python", "dyn_dns.py"]
