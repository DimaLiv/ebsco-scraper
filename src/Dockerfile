ARG PYTHON_IMAGE_VERSION

FROM python:${PYTHON_IMAGE_VERSION} AS base
ARG CHROME_DRIVER_ARCH=linux64
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
WORKDIR /app
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get -y update && \
    apt-get install -y google-chrome-stable && \
    apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/`curl -sS \
    https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE`/${CHROME_DRIVER_ARCH}/chromedriver-${CHROME_DRIVER_ARCH}.zip  && \
    unzip /tmp/chromedriver.zip chromedriver-${CHROME_DRIVER_ARCH}/chromedriver -d /usr/local/bin/
COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
