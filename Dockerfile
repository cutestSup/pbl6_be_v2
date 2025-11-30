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

# Copy và install VietOCR package
COPY vietocr /app/vietocr
WORKDIR /app/vietocr
RUN pip install -e .

# Quay lại thư mục làm việc chính
WORKDIR /app

# Copy toàn bộ mã nguồn còn lại
COPY . .

# Mở port 8000
EXPOSE 8000

# Tải Model Weights khi container khởi động (thay vì lúc build)
CMD python download_weights.py && uvicorn app.main:app --host 0.0.0.0 --port 8000