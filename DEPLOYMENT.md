# Deploy Guide - PBL6 Backend

## Option 1: Railway (Recommended - Easiest)

### 1. Setup Database
1. Go to https://neon.tech
2. Sign up and create new project
3. Copy the **Connection String** (DATABASE_URL)

### 2. Deploy to Railway
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add environment variables:
   ```
   DATABASE_URL=postgresql://...
   CLOUDINARY_CLOUD_NAME=dp1nxkame
   CLOUDINARY_API_KEY=312795443157921
   CLOUDINARY_API_SECRET=bVvAANzwfku5Oj2s8J-AFl3TGhU
   FIREBASE_CREDENTIALS=<paste entire firebase-key.json content>
   ```
6. Railway will auto-deploy using Dockerfile

### 3. Upload Model Weights
**Option A: Google Drive**
1. Upload `app/weights/*.pth` to Google Drive
2. Get shareable link (Anyone with link can view)
3. Extract file ID from link
4. Update `download_weights.py` with file IDs
5. Add to Dockerfile before CMD:
   ```dockerfile
   RUN python download_weights.py
   ```

**Option B: Cloudinary**
1. Upload weights as raw files to Cloudinary
2. Update code to download from Cloudinary URLs

### 4. Firebase Credentials
**Option A: Environment variable (recommended)**
```python
# app/firebase_init.py
import os
import json

def initialize_firebase():
    if not firebase_admin._apps:
        cred_json = os.getenv('FIREBASE_CREDENTIALS')
        if cred_json:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
        else:
            cred = credentials.Certificate('app/config/firebase-key.json')
        firebase_admin.initialize_app(cred)
```

**Option B: Secret file in deployment**
Upload firebase-key.json through Railway's file upload feature

---

## Option 2: Render.com (Free tier)

1. Go to https://render.com
2. Create new Web Service
3. Connect GitHub repo
4. Use `render.yaml` configuration
5. Add environment variables in Render dashboard
6. Deploy

---

## Option 3: Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/pbl6-ocr

# Deploy to Cloud Run
gcloud run deploy pbl6-ocr \
  --image gcr.io/YOUR_PROJECT_ID/pbl6-ocr \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL,CLOUDINARY_CLOUD_NAME=$CLOUDINARY_CLOUD_NAME
```

---

## Testing Deployment

1. Get your deployed URL (e.g., `https://pbl6-ocr.up.railway.app`)
2. Test health endpoint:
   ```bash
   curl https://your-domain.com/health
   ```
3. Test in Postman with `/ocr/upload`
4. Update frontend API_BASE_URL to your deployed URL

---

## Important Notes

⚠️ **Model weights are LARGE** (>500MB total)
- Don't commit to git
- Use Google Drive or Cloudinary
- Download on first deployment

⚠️ **Free tier limits:**
- Railway: $5 credit/month
- Render: 750 hours/month, sleeps after 15min inactive
- Consider paid plan for production

⚠️ **Database:**
- Neon.tech: 3GB free
- Supabase: 500MB free
- Railway PostgreSQL: $5/month

## Troubleshooting

**Deployment fails:**
- Check logs in Railway/Render dashboard
- Verify environment variables
- Ensure requirements.txt includes all dependencies

**Model loading error:**
- Verify weights downloaded correctly
- Check file paths in pipeline initialization
- Ensure sufficient memory (upgrade plan if needed)

**Database connection error:**
- Verify DATABASE_URL format
- Check PostgreSQL is running
- Ensure SSL mode if required
