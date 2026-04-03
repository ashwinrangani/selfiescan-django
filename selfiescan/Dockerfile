# -------- STAGE 1: BUILDER --------
FROM python:3.12-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libpq-dev \
    git \
    pkg-config \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt
    
# -------- STAGE 2: PRODUCTION --------
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libpq5 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libopenblas-dev \
    liblapack-dev \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy installed Python packages
COPY --from=builder /install /usr/local

# Copy project
COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Start the app (for production, use Gunicorn or Daphne for Channels)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "mysite.asgi:application"]

