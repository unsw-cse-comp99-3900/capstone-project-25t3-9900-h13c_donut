# 1) Base image with CUDA 11.8 + PyTorch 2.1.2
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Australia/Sydney \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 2) System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tzdata \
        ffmpeg \
        build-essential \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3) Pre-copy requirements
COPY requirements.txt .

# 4) Install torch GPU first, then other deps
RUN pip install --no-cache-dir \
        "torch==2.1.2+cu118" "torchaudio==2.1.2+cu118" \
        --index-url https://download.pytorch.org/whl/cu118 \
    && pip install --no-cache-dir -r requirements.txt

# 5) Copy project (excluding models via .dockerignore)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]