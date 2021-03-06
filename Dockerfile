FROM python:3-stretch

LABEL maintainer="jacques@supcik.net"

RUN apt-get update && apt-get install -y \
      libasound2 \
      libatk-bridge2.0-0 \
      libgtk-3-0 \
      libnss3 \
      libx11-xcb1 \
      libxtst6 \
  && python -m pip install --upgrade pip setuptools


ADD https://github.com/Yelp/dumb-init/releases/download/v1.2.2/dumb-init_1.2.2_amd64 /usr/local/bin/dumb-init
RUN chmod +x /usr/local/bin/dumb-init
ENTRYPOINT ["dumb-init", "--"]

RUN python -m pip install \
  hypercorn \
  pyppeteer \
  quart

COPY app /app
WORKDIR /app

#ENTRYPOINT []
CMD hypercorn api:app -b 0.0.0.0:${PORT:-5000}