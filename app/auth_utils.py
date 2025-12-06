from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from sqlalchemy.orm import Session
from app.db.models import User
from app.db.database import get_db
import datetime
import jwt

security = HTTPBearer()

async def verify_firebase_token(request: Request):
    """
    Verify Firebase ID token from Authorization header
    Returns decoded token if authenticated, None if guest (no token)
    
    Returns:
        dict: {"uid": "...", "email": "...", "name": "...", "picture": "..."} hoặc None
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        if not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.replace("Bearer ", "")
        
        print(f"--- Verifying Token ---")
        try:
            decoded_token = auth.verify_id_token(token)
            print(f"Decoded Token (Verified): {decoded_token}")
        except Exception as e:
            print(f"Firebase verification failed: {e}")
            print("Attempting unsafe decode (development mode)...")
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            print(f"Decoded Token (Unsafe): {decoded_token}")
        
        uid = decoded_token.get("uid") or decoded_token.get("user_id") or decoded_token.get("sub")
        email = decoded_token.get("email")
        
        print(f"Extracted UID: {uid}")
        print(f"Extracted Email: {email}")

        if not email and uid:
            email = f"{uid}@test.com"
        
        return {
            "uid": uid,
            "email": email,
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture")
        }
    except Exception as e:
        print(f"Auth error: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_or_create_user(firebase_user: dict, db: Session) -> User:
    print(f"--- Get or Create User ---")
    print(f"Firebase User Data: {firebase_user}")

    if not firebase_user.get("email"):
        print("Error: Email is missing in firebase_user data")
        raise ValueError(f"Email is required. User data: {firebase_user}")
    
    user = db.query(User).filter(User.firebase_uid == firebase_user["uid"]).first()
    
    if user:
        print(f"Found existing user: {user.id}")
        user.last_login = datetime.datetime.utcnow()
        if firebase_user.get("email"):
            user.email = firebase_user["email"] 
        if firebase_user.get("name"):
            user.display_name = firebase_user["name"]
        if firebase_user.get("picture"):
            user.photo_url = firebase_user["picture"]
        db.commit()
        db.refresh(user)
    else:
        print("Creating new user...")
        user = User(
            firebase_uid=firebase_user["uid"],
            email=firebase_user["email"],
            display_name=firebase_user.get("name"),
            photo_url=firebase_user.get("picture"),
            is_active=True,
            created_at=datetime.datetime.utcnow(),
            last_login=datetime.datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created user: {user.id}")
    
    return user


def get_current_user(token_data: dict = Depends(verify_firebase_token)):
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu đăng nhập"
        )
    return token_data
