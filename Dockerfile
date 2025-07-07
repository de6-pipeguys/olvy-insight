FROM apache/airflow:2.9.1

# 🧨 1. Chrome 설치는 루트 권한이 필요하므로
USER root

# ✅ 크롬 및 기타 의존 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    --no-install-recommends && \
    wget -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i /tmp/chrome.deb || apt-get -fy install && \
    rm /tmp/chrome.deb

# 🔽 2. airflow 유저로 돌아와서
USER airflow

# ✅ requirements.txt 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
