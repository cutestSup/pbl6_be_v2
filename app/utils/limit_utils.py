from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db.models import User, UserLimit

guest_store = {} 

MAX_GUEST_SCAN = 3
WINDOW = timedelta(hours=24)

def increment_guest(ip):
    now = datetime.utcnow()
    data = guest_store.get(ip)
    if not data or now >= data["reset_at"]:
        guest_store[ip] = {"count": 1, "reset_at": now + WINDOW}
        return 1
    data["count"] += 1
    return data["count"]