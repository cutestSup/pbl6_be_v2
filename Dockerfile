FROM python:3.10-slim

WORKDIR /app

# Set PYTHONPATH to include vietocr directory
ENV PYTHONPATH=/app/vietocr:$PYTHONPATH

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy and install VietOCR local package first
COPY vietocr /app/vietocr
WORKDIR /app/vietocr
RUN pip install -e . && pip list | grep vietocr
WORKDIR /app

COPY . .
RUN python download_weights.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
