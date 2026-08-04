FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Avoid tzdata interactive prompt during apt-get install
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
# Whisper and PyTorch with CUDA support
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default to running the web UI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
