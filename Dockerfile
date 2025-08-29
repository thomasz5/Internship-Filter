FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for Chrome and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg unzip \
    ca-certificates fonts-liberation \
    libasound2 libatk-bridge2.0-0 libnspr4 libnss3 libgbm1 \
    libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libxshmfence1 libgtk-3-0 xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default environment for remote selenium and redis
ENV USE_REMOTE_SELENIUM=true \
    SELENIUM_REMOTE_URL=http://selenium:4444/wd/hub \
    REDIS_URL=redis://redis:6379/0

CMD ["python", "main.py", "worker", "--timeout", "10"]

