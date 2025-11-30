FROM python:3.10-slim

WORKDIR /app

# Thiết lập PYTHONPATH
ENV PYTHONPATH=/app/vietocr:$PYTHONPATH

# Cài đặt thư viện hệ thống
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# --- QUAN TRỌNG: Cài PyTorch bản CPU (Siêu nhẹ) trước ---
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
# --------------------------------------------------------

# Copy và cài các thư viện còn lại
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (Không copy thư mục rác nhờ .dockerignore)
COPY vietocr /app/vietocr
COPY . .

# Mở port
EXPOSE 8000

# Chạy lệnh tải weights trước khi bật server
# (Vì image nhẹ rồi nên lệnh này sẽ chạy nhanh và không gây timeout nữa)
CMD python download_weights.py && uvicorn app.main:app --host 0.0.0.0 --port 8000