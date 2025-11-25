# PBL6 Backend - Vietnamese OCR API

Backend API for Vietnamese text recognition using DBNet (text detection) and VietOCR (text recognition).

## Project Structure

```
pbl6_be_v2/
├─ app/
│   ├─ main.py                 # FastAPI application entry point
│   ├─ firebase_init.py        # Firebase Admin SDK initialization
│   ├─ auth_utils.py           # Firebase authentication utilities
│   ├─ config/
│   │   ├─ firebase-key.json   # Firebase service account key (not in git)
│   │   ├─ myconfig.yml        # VietOCR configuration
│   │   └─ icdar2015_config.yaml  # DBNet configuration
│   ├─ weights/
│   │   ├─ dbnet_model.pth     # DBNet model weights (download separately)
│   │   └─ vietocr_model.pth   # VietOCR model weights (optional)
│   ├─ db/
│   │   ├─ database.py         # Database configuration
│   │   └─ models.py           # SQLAlchemy models
│   ├─ ocr/
│   │   ├─ preprocess.py       # Image preprocessing utilities
│   │   ├─ dbnet_model.py      # DBNet text detection
│   │   ├─ vietocr_model.py    # VietOCR text recognition
│   │   └─ pipeline.py         # Complete OCR pipeline
│   ├─ routes/
│   │   └─ ocr_routes.py       # OCR API endpoints
│   └─ utils/
│       ├─ cloudinary_utils.py # Cloudinary image upload
│       └─ limit_utils.py      # User rate limiting
└─ requirements.txt            # Python dependencies
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Firebase

1. Create a Firebase project at https://console.firebase.google.com
2. Generate a service account key
3. Save it as `app/config/firebase-key.json`

### 3. Configure Database

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

## Authentication

The API uses Firebase Authentication. Clients must include a valid Firebase ID token in the Authorization header.

## Rate Limiting

- Default: 100 requests per day per user
- Configurable in `UserLimit` model

## Development

1. Copy `.env.example` to `.env` and update values
2. Initialize database: 
   ```python
   from app.db.database import init_db
   init_db()
   ```
3. Run with hot reload:
   ```bash
   uvicorn app.main:app --reload
   ```

## License

MIT
