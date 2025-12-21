# PBL6 Backend - Vietnamese OCR API

Backend API for Vietnamese text recognition using DBNet (text detection) and VietOCR (text recognition).

## Setup

### 1. Install Dependencies

pip install -r requirements.txt

### 2. Configure Database

Create a PostgreSQL database and update the connection string in `.env`:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/pbl6_db
```

### 4. Configure Cloudinary (Optional)

Sign up at https://cloudinary.com and add your credentials to `.env`:

```bash
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 5. Download Model Weights

Place your model weights in the `app/weights/` directory:
- `dbnet_model.pth` - DBNet text detection model
- `vietocr_model.pth` - VietOCR text recognition model (optional)

## Running the Application
.\.venv\Scripts\Activate.ps1
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

## API Endpoints

### Health Check
- `GET /` - Welcome message
- `GET /health` - Health check

### OCR
- `POST /api/v1/ocr` - Perform OCR with bounding boxes
- `POST /api/v1/ocr/simple` - Perform simple OCR (text only)
- `GET /api/v1/ocr/history` - Get OCR history

All OCR endpoints require Firebase authentication token in the `Authorization` header:
```
Authorization: Bearer <firebase-id-token>
```
