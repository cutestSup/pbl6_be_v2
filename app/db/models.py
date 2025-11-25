from sqlalchemy import Column, Integer, String, Text, Double, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import datetime
from app.db.database import Base  

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=False)  
    email = Column(String, unique=True, index=True, nullable=False)  
    display_name = Column(String, nullable=True) 
    photo_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)  
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, default=datetime.datetime.utcnow)

    records = relationship("OcrRecord", back_populates="owner")

class OcrRecord(Base):
    __tablename__ = 'ocr_records'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    processed_time = Column(Double)
    image_url = Column(Text, nullable=False)
    text_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="records")