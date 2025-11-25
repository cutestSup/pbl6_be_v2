from fastapi import APIRouter, Depends
from app.db.database import get_db
from app.db.models import User, OcrRecord
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/users")
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    
    result = []
    for user in users:
        records_count = db.query(OcrRecord).filter(OcrRecord.user_id == user.id).count()
        result.append({
            "id": user.id,
            "firebase_uid": user.firebase_uid,
            "email": user.email,
            "display_name": user.display_name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "ocr_records_count": records_count
        })
    
    return {
        "success": True,
        "total": len(result),
        "users": result
    }

@router.get("/history/{firebase_uid}")
async def get_user_history(
    firebase_uid: str,
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if not user:
        return {
            "success": False,
            "error": f"User with firebase_uid '{firebase_uid}' not found",
            "available_users": [u.firebase_uid for u in db.query(User).limit(10).all()]
        }
    
    total = db.query(OcrRecord).filter(OcrRecord.user_id == user.id).count()
    
    records = db.query(OcrRecord)\
        .filter(OcrRecord.user_id == user.id)\
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
        "user": {
            "id": user.id,
            "firebase_uid": user.firebase_uid,
            "email": user.email,
            "display_name": user.display_name
        },
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total,
        "history": history
    }

@router.get("/all-records")
async def get_all_records(db: Session = Depends(get_db), limit: int = 50):

    records = db.query(OcrRecord)\
        .order_by(OcrRecord.created_at.desc())\
        .limit(limit)\
        .all()
    
    result = []
    for record in records:
        user = db.query(User).filter(User.id == record.user_id).first()
        result.append({
            "id": record.id,
            "user_id": user.id if user else None,
            "user_email": user.email if user else "Unknown",
            "user_firebase_uid": user.firebase_uid if user else "Unknown",
            "user_display_name": user.display_name if user else "Unknown",
            "image_url": record.image_url,
            "text_url": record.text_url,
            "processing_time": record.processed_time,
            "created_at": record.created_at.isoformat() if record.created_at else None
        })
    
    return {
        "success": True,
        "total": len(result),
        "records": result
    }
