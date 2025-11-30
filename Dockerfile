FROM python:3.10-slim

WORKDIR /app

# Thiết lập PYTHONPATH để nhận diện thư viện vietocr local
ENV PYTHONPATH=/app/vietocr:$PYTHONPATH

# Cài đặt các thư viện hệ thống cần thiết (đã sửa cho Debian Trixie)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy và cài đặt các thư viện Python từ requirements.txt trước
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- SỬA LỖI Ở ĐÂY ---
# Chỉ copy thư mục vietocr vào, KHÔNG chạy lệnh pip install -e . nữa
COPY vietocr /app/vietocr
# ---------------------

# Quay lại thư mục làm việc chính
WORKDIR /app

# Copy toàn bộ mã nguồn còn lại
COPY . .

# Tải Model Weights
RUN python download_weights.py

# Mở port 8000
EXPOSE 8000

# Lệnh chạy server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]