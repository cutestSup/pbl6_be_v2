from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import firebase_admin
from firebase_admin import auth
import requests
import os

router = APIRouter(prefix="/token", tags=["Token Management"])

class RefreshTokenRequest(BaseModel):
    firebase_uid: str
    email: Optional[str] = None

class RefreshTokenResponse(BaseModel):
    id_token: str
    expires_in: int
    firebase_uid: str
    email: str
    message: str

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    try:
        email = request.email or f"{request.firebase_uid}@test.com"
        
        custom_token = auth.create_custom_token(
            request.firebase_uid,
            {'email': email}
        )
        
        FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "AIzaSyBvygxac8xfgJuDtUPNWSXox8fSkeg0cUQ")
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_API_KEY}"
        
        response = requests.post(url, json={
            "token": custom_token.decode('utf-8'),
            "returnSecureToken": True
        })
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to exchange token: {response.text}"
            )
        
        data = response.json()
        id_token = data.get('idToken')
        expires_in = int(data.get('expiresIn', 3600))
        
        return RefreshTokenResponse(
            id_token=id_token,
            expires_in=expires_in,
            firebase_uid=request.firebase_uid,
            email=email,
            message=f"Token refreshed successfully. Expires in {expires_in} seconds."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/batch-refresh")
async def batch_refresh_tokens():
    """
    Refresh tokens for all 10 sample users
    
    Returns a dictionary with tokens for user_001 to user_010
    """
    try:
        SAMPLE_USERS = [
            {"uid": "user_001", "email": "nguyen.van.a@example.com", "name": "Nguyễn Văn A"},
            {"uid": "user_002", "email": "tran.thi.b@example.com", "name": "Trần Thị B"},
            {"uid": "user_003", "email": "le.van.c@example.com", "name": "Lê Văn C"},
            {"uid": "user_004", "email": "pham.thi.d@example.com", "name": "Phạm Thị D"},
            {"uid": "user_005", "email": "hoang.van.e@example.com", "name": "Hoàng Văn E"},
            {"uid": "user_006", "email": "vu.thi.f@example.com", "name": "Vũ Thị F"},
            {"uid": "user_007", "email": "dang.van.g@example.com", "name": "Đặng Văn G"},
            {"uid": "user_008", "email": "bui.thi.h@example.com", "name": "Bùi Thị H"},
            {"uid": "user_009", "email": "do.van.i@example.com", "name": "Đỗ Văn I"},
            {"uid": "user_010", "email": "ngo.thi.k@example.com", "name": "Ngô Thị K"},
        ]
        
        FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "AIzaSyBvygxac8xfgJuDtUPNWSXox8fSkeg0cUQ")
        tokens = {}
        
        for user in SAMPLE_USERS:
            custom_token = auth.create_custom_token(
                user['uid'],
                {'email': user['email']}
            )
            
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_API_KEY}"
            response = requests.post(url, json={
                "token": custom_token.decode('utf-8'),
                "returnSecureToken": True
            })
            
            if response.status_code == 200:
                data = response.json()
                tokens[user['uid']] = {
                    "name": user['name'],
                    "email": user['email'],
                    "token": data.get('idToken'),
                    "expires_in": int(data.get('expiresIn', 3600))
                }
        
        return {
            "message": f"Successfully refreshed {len(tokens)} tokens",
            "tokens": tokens,
            "expires_in_seconds": 3600
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch refresh failed: {str(e)}"
        )
