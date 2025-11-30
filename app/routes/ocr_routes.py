from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Depends
from app.auth_utils import verify_firebase_token, get_current_user, get_or_create_user
# from app.utils.limit_utils import increment_guest, MAX_GUEST_SCAN  
from app.ocr.pipeline import OCRPipeline
from app.utils.cloudinary_utils import upload_image_bytes, upload_text_file
from app.db.database import SessionLocal, get_db
from app.db.models import OcrRecord, User 
from sqlalchemy.orm import Session
import io
import datetime

router = APIRouter()

# Lazy load pipeline only when needed (saves RAM)
pipeline = None

def get_pipeline():
    global pipeline
    if pipeline is None:
        pipeline = OCRPipeline(
            dbnet_weight="app/weights/model_best_100_03.pth",
            dbnet_cfg="app/config/icdar2015_resnet18_FPN_DBhead_polyLR.yaml",
            vietocr_cfg="app/config/myconfig.yml",
            vietocr_weight="app/weights/mymodelOCR.pth"
        )
    return pipeline

@router.post("/upload")
async def upload_image(
    request: Request, 
    file: UploadFile = File(..., description="Image file containing Vietnamese text"),
    db: Session = Depends(get_db)
):
    """
    Upload ảnh và OCR
    
    - **Guest** (không token): Vẫn xử lý OCR nhưng KHÔNG lưu vào DB
    - **User** (có token): Xử lý OCR VÀ lưu vào DB
    """
    firebase_user = await verify_firebase_token(request)  

    contents = await file.read()
    res = get_pipeline().process(contents)
    img_url = upload_image_bytes(contents, folder="ocr_uploads", resource_type="image")
    
    text_content = "\n".join([r["text"] for r in res["results"]])
    text_url = upload_text_file(text_content, filename=f"result_{file.filename}.txt", folder="ocr_texts")

    if firebase_user:
        db_user = get_or_create_user(firebase_user, db)
        
        rec = OcrRecord(
            user_id=db_user.id,
            image_url=img_url, 
            text_url=text_url, 
            processed_time=res["processing_time"]
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

    return {"image_url": img_url, "text_url": text_url, "results": res["results"], "processing_time": res["processing_time"]}


@router.post("/auth/verify")
async def verify_user_token(
    request: Request, 
    db: Session = Depends(get_db)
):
    try:
        firebase_user = await verify_firebase_token(request)
        
        if not firebase_user:
            raise HTTPException(
                status_code=401,
                detail="Token không hợp lệ hoặc không được cung cấp"
            )
        
        db_user = get_or_create_user(firebase_user, db)
        
        return {
            "success": True,
            "user": {
                "id": db_user.id,
                "firebase_uid": db_user.firebase_uid,
                "email": db_user.email,
                "display_name": db_user.display_name,
                "photo_url": db_user.photo_url,
                "is_active": db_user.is_active,
                "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
                "last_login": db_user.last_login.isoformat() if db_user.last_login else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in /auth/verify: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/history")
async def get_ocr_history(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    """
    Get OCR history for authenticated user
    
    **Query Parameters:**
    - limit: Number of records to return (default: 10, max: 100)
    - offset: Number of records to skip (default: 0)
    
    **Returns:**
    - List of OCR records with pagination
    """
    user = await verify_firebase_token(request)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Vui lòng đăng nhập để xem lịch sử"
        )
    
    if limit > 100:
        limit = 100
    
    db_user = db.query(User).filter(User.firebase_uid == user["uid"]).first()
    
    if not db_user:
        return {
            "success": True,
            "total": 0,
            "limit": limit,
            "offset": offset,
            "history": []
        }
    
    total = db.query(OcrRecord).filter(OcrRecord.user_id == db_user.id).count()
    
    records = db.query(OcrRecord)\
        .filter(OcrRecord.user_id == db_user.id)\
        .order_by(OcrRecord.created_at.desc())\
        .limit(limit)\
        .offset(offset)\
        .all()
    
    history = []
    for record in records:
        history.append({
            "id": record.id,
            "image_url": record.image_url,
            "text_url": record.text_url,
            "processing_time": record.processed_time,
            "created_at": record.created_at.isoformat() if record.created_at else None
        })
    
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total,
        "history": history
    }


@router.get("/history/{record_id}")
async def get_ocr_record_detail(
    record_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = await verify_firebase_token(request)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Vui lòng đăng nhập"
        )
    
    db_user = db.query(User).filter(User.firebase_uid == user["uid"]).first()
    
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User không tồn tại"
        )
    
    record = db.query(OcrRecord)\
        .filter(OcrRecord.id == record_id, OcrRecord.user_id == db_user.id)\
        .first()
    
    if not record:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy bản ghi hoặc bạn không có quyền truy cập"
        )
    
    return {
        "success": True,
        "record": {
            "id": record.id,
            "image_url": record.image_url,
            "text_url": record.text_url,
            "processing_time": record.processed_time,
            "created_at": record.created_at.isoformat() if record.created_at else None
        }
    }


@router.delete("/history/{record_id}")
async def delete_ocr_record(
    record_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = await verify_firebase_token(request)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Vui lòng đăng nhập"
        )
    
    db_user = db.query(User).filter(User.firebase_uid == user["uid"]).first()
    
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User không tồn tại"
        )
    
    record = db.query(OcrRecord)\
        .filter(OcrRecord.id == record_id, OcrRecord.user_id == db_user.id)\
        .first()
    
    if not record:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy bản ghi hoặc bạn không có quyền xóa"
        )
    
    db.delete(record)
    db.commit()
    
    return {
        "success": True,
        "message": "Đã xóa bản ghi thành công"
    }
