import firebase_admin
from firebase_admin import credentials
import os
import json

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if firebase_admin._apps:
        print("ℹ️  Firebase already initialized")
        return
    
    try:
        cred_json = os.getenv('FIREBASE_CREDENTIALS')
        if cred_json:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
        else:
            cred_path = os.path.join(os.path.dirname(__file__), "config", "firebase-key.json")
            if not os.path.exists(cred_path):
                raise FileNotFoundError(f"Firebase key not found at {cred_path}")
            cred = credentials.Certificate(cred_path)

        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        raise