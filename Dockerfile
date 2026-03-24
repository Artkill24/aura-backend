FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.3.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p temp outputs
RUN python3 -c "from transformers import pipeline;     pipeline('image-classification', model='dima806/deepfake_vs_real_image_detection');     print('Model 1 cached')" || echo "Model 1 cache failed"
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
