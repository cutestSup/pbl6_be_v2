import cloudinary
import cloudinary.uploader
import os
import io
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_image_bytes(image_bytes, folder="ocr_uploads", resource_type="image"):
    """
    Upload bytes to Cloudinary
    
    Args:
        image_bytes: Bytes to upload
        folder: Cloudinary folder name
        resource_type: 'image', 'raw', or 'auto'
    
    Returns:
        Secure URL of uploaded file
    """
    try:
        res = cloudinary.uploader.upload(
            image_bytes, 
            resource_type=resource_type, 
            folder=folder
        )
        return res.get("secure_url")
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None

def upload_text_file(text_content, filename="result.txt", folder="ocr_texts"):
 
    try:
        if isinstance(text_content, str):
            text_bytes = text_content.encode("utf-8")
        else:
            text_bytes = text_content
        
        text_file = io.BytesIO(text_bytes)
        
        res = cloudinary.uploader.upload(
            text_file,
            resource_type="raw",
            folder=folder,
            public_id=filename
        )
        return res.get("secure_url")
    except Exception as e:
        print(f"Cloudinary text upload error: {e}")
        return None
