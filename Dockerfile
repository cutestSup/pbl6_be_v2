FROM python:3.10-slim

WORKDIR /app

# --- BƯỚC 1: Cài thư viện hệ thống ---
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# --- BƯỚC 2: Cài PyTorch bản CPU (Nhẹ, tránh lỗi Build Timeout) ---
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# --- BƯỚC 3: Cài các thư viện khác (bao gồm vietocr) ---
COPY requirements.txt .
COPY vietocr ./vietocr
RUN pip install --no-cache-dir -r requirements.txt

# --- BƯỚC 4: Chỉ copy mã nguồn chính (BỎ đoạn copy vietocr) ---
# Xóa dòng COPY vietocr và ENV PYTHONPATH đi vì không cần thiết nữa
COPY . .

# Thiết lập PYTHONPATH để Python tìm thấy các module trong thư mục gốc (bao gồm segmentation)
ENV PYTHONPATH=/app

# Mở port
EXPOSE 8000

# Chạy lệnh tải weights và server
CMD python download_weights.py && uvicorn app.main:app --host 0.0.0.0 --port 8000