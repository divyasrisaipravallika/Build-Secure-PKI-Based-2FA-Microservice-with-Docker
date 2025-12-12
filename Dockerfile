# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim AS builder
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and build wheels
COPY requirements.txt .
RUN python -m pip install --upgrade pip wheel setuptools
RUN pip wheel --wheel-dir=/wheels -r requirements.txt


# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim
ENV TZ=UTC
WORKDIR /app

# Install cron + timezone data
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    cron \
    tzdata \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Set timezone to UTC
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime && echo "UTC" > /etc/timezone


# ============================================
# Install Python wheels
# ============================================
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*


# ============================================
# Copy application code
# ============================================
COPY . /app


# ============================================
# Setup cron job
# ============================================
# Copy cron file (must be LF)
COPY cron/2fa-cron /etc/cron.d/2fa-cron
RUN chmod 0644 /etc/cron.d/2fa-cron

# Install cron file
RUN crontab /etc/cron.d/2fa-cron


# ============================================
# Prepare volume mount points
# ============================================
RUN mkdir -p /data /cron && chmod 700 /data && chmod 755 /cron


# ============================================
# Secure key files
# ============================================
RUN if [ -f "/app/student_private.pem" ]; then chmod 600 /app/student_private.pem; fi
RUN if [ -f "/app/student_public.pem" ]; then chmod 644 /app/student_public.pem; fi
RUN if [ -f "/app/instructor_public.pem" ]; then chmod 644 /app/instructor_public.pem; fi


# ============================================
# Networking
# ============================================
EXPOSE 8080
VOLUME ["/data", "/cron"]


# ============================================
# Entrypoint: Start cron + FastAPI server
# ============================================
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
