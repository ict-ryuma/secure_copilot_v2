FROM python:3.11-slim

WORKDIR /app

# Install system dependencies + cron
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    cron \
    curl \
    bash \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app code
# COPY . .

# Copy crontab file
COPY crontab.txt /etc/cron.d/s3-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/s3-cron

# Apply cron job
RUN crontab /etc/cron.d/s3-cron

# Copy start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# CMD to run cron + start.sh (your main app)
# CMD ["sh", "-c", "cron && /start.sh"]
CMD sh -c "cron -L 15 & /start.sh"


