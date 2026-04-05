FROM python:3.11-slim

# Install system dependencies + FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create cache dir
RUN mkdir -p /tmp/neko_cache

CMD ["python", "__main__.py"]
