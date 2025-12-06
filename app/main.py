import sys
import os
# Thêm đường dẫn đến folder vietocr local
vietocr_path = os.path.join(os.path.dirname(__file__), "..", "vietocr")
vietocr_path = os.path.abspath(vietocr_path)
if vietocr_path not in sys.path:
    sys.path.insert(0, vietocr_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import SecurityScheme, SecuritySchemeType, HTTPBearer
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from app.routes import ocr_routes, test_routes, token_routes
from app.firebase_init import initialize_firebase

# Initialize Firebase Admin SDK
initialize_firebase()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    ocr_routes.initialize_pipeline()
    yield
    # Clean up the ML models and release the resources

app = FastAPI(
    title="PBL6 OCR API",
    description="Vietnamese OCR API with DBNet + VietOCR",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True
    }
)

# Custom OpenAPI schema with global security
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="PBL6 OCR API",
        version="1.0.0",
        description="Vietnamese OCR API with DBNet + VietOCR",
        routes=app.routes,
    )
    
    # Add Bearer token security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your Firebase ID token"
        }
    }
    
    # Apply security globally to all endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["get", "post", "put", "delete", "patch"]:
                openapi_schema["paths"][path][method]["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ocr_routes.router, prefix="/ocr", tags=["OCR"])
app.include_router(test_routes.router, prefix="/test", tags=["Testing"])
app.include_router(token_routes.router, tags=["Token Management"])

@app.get("/health")
async def health():
    return {"status": "ok"}