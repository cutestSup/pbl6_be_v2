FROM python:3.10-slim

WORKDIR /app

# Thiết lập PYTHONPATH để ưu tiên nhận diện thư viện trong thư mục /app/vietocr
ENV PYTHONPATH=/app/vietocr:$PYTHONPATH

# Cài đặt thư viện hệ thống (đã fix cho Debian Trixie)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt thư viện Python từ requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- SỬA LỖI TẠI ĐÂY ---
# Chỉ copy code vào, KHÔNG chuyển thư mục và KHÔNG chạy pip install -e .
COPY vietocr /app/vietocr
# -----------------------

# Quay lại thư mục làm việc chính
WORKDIR /app

# Copy toàn bộ mã nguồn dự án
COPY . .

# Mở port
EXPOSE 8000

# Chạy lệnh tải weights trước khi bật server để tránh lỗi Build Timeout
CMD python download_weights.py && uvicorn app.main:app --host 0.0.0.0 --port 8000