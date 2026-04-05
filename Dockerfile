FROM python:3.11-slim

# Install system deps + FFmpeg + git (needed for git pip install)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    wget \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create cache directory
RUN mkdir -p /tmp/neko_cache

CMD ["python", "__main__.py"]
