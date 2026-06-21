from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. बिना JSON फ़ाइल के सीधे फायरबेस इनिशियलाइज़ेशन
firebase_config = {
    "type": "service_account",
    "project_id": "marva-8280e",  # अपना प्रोजेक्ट आईडी यहाँ डालें
    "private_key_id": "9df6d1e8da0673546d98fe387c271b6479ed651c", # अपनी प्राइवेट की आईडी डालें
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDEmrnjLJOZAZcC\nP5z/RFbz7VDqK/brXj2jd5QzjyJmb8Nb2FbVWiMNi0uI6Bzvnk/YzZofvqiHmLme\nlqDmugB0vNiuQr3JAaZuF1V/K7FcJ14MPTO0ZJrtz1fnFA/qcNFDw7ViHUwSOnkO\nAcT6+65pkq4HNoxu2+dBmU0F0XldDSmcpxOk8aVJ8DYgS1Uui5DvZSRBozf6oumn\nzX03szJo3PaBD55RRVP74GXmAQksTPj9pkF7krBNNDTF0tp8hjm2WwzEuRBgyQZJ\n46FFLxIIl0r7aymblW5X9NLXhIBRp69bmirHSH4bE9vpH2TW19QDNJ5gUDLgAGTW\ng1zGFV5jAgMBAAECggEATsB5oFVtQ/c+kXCAx0GNIQVZCYwVyr8DqrSOAT8e9PBk\nzSfx1GFYNCctWQg8+wCrlDj7OScKY9JZ2/wTNIiiASDaHKdwVRFbpLKlFR0f3L2K\nLxXe3a4E3yhUWiQPogWR1XaR89yvaYfRkLpFuJFTEkfmfM4tX4Snc//fuepoFkyp\nB1oD9stKp/+jfbkE49s4XQcraxGC2F8E66JyIoOy9fBDxLutMpnnCfUYR1mmS7fc\nnyoGZioFbU+mow1L2z+y9nLnMF5pjc2On+r9zC/f2jI6+S7NrpN4gUkfxPRF7ppZ\nzk9JLFeorJdZ/PxGzm7+OFtHaqA5sQeLo5RV5kCZoQKBgQDrA+V9sK3w16hPd2m0\nUYCaj5+APzL1PlxpttxGx3ZUhLmzO2XTrml9j1myNpXa2q12kNvhqs7MbbDJxg8p\nAg9BaJWax2KwKl3TvHhz3LVLGWDqzuPYBkTQqaWg5kU15qC3izCthVWDAmBkBPCC\nRNy/FhAvM2AdYO56EtAyqBNLYQKBgQDWKNCIP/SkdxhrY2PHrUq8uApUAhQRWnYG\n/iDFCOx2lXjzNaz4qD2jI/To6oUyhy22Te3wRbR4u0Acg7FP3feH8lvmYny5wu/C\ndJghlRBxP9R1+ZjUU789Zg1NLa8Jt0didB/yMgLsx0Noys+qVtQDskLFAJSM3a9L\nkxAZf88kQwKBgHR5GeORDKOwPdokdF7JhdMUGxiUOc0RevtphQIPGLYKkX4ikfS3\nG9D+mpWYN+yfNBju8gqFfLgUJOnbHuhT/PuNuZdb+a0VUir93TSOzcrKaR32KzWE\n5dYEPfHgLazo//33Hcjhq9+h7eOkDw6A0mZhqOO7sobc41PcvxJb+jQBAoGAOvDO\nu8EGXsFcWinni0wZVqk8RnSv+zqvYytL746OLfDjceRi76i2FhFOVVA+SnLD1PnL\ns6YrjlLSyUZBZZ7MgoDkZBrVAvcwr48RU6TH+rM7kSCZvE40Qvy0Snp5Qy5LGkCl\nji3PekU5Oz0ePF5bSY0lLT0EpWRZ223lL29qnisCgYEAoHfP6+JreU3bWlCqR7Qz\ntwu0fy70NKo1TpMUfxZyK2ITAjwvTiQ/nFHd+ZnGAwgzdJoj0XWcQkW9dOLFbg98\n/JJ/fMI7bJRgM0/XyCJG8B8J+GNlFYkxDxg2s4FZrUtfwGFAM1z0aQinJ/FLfsn8\nxmwxw41gB865uSVp4s3py4o=\n-----END PRIVATE KEY-----\n",, # पूरी प्राइवेट की यहाँ डालें (\n के साथ)
    "client_email": "firebase-adminsdk-fbsvc@marva-8280e.iam.gserviceaccount.com", # अपना क्लाइंट ईमेल डालें
    "token_uri": "https://oauth2.googleapis.com/token"
}

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Firebase Init Error: {str(e)}")

db = firestore.client()

class TrainRequest(BaseModel):
    bizName: str
    bizCategory: str
    bizProducts: str
    aiTone: str
    aiLang: str

class LinkWhatsAppRequest(BaseModel):
    phone: str
    bizName: str
    bizCategory: str
    bizProducts: str
    aiTone: str
    aiLang: str

@app.post("/train-ai/")
async def train_ai_core(data: TrainRequest):
    if not data.bizName or not data.bizCategory or not data.bizProducts:
        raise HTTPException(status_code=400, detail="Mandatory fields missing")
    return {"status": "success", "message": "Local sync complete"}

@app.post("/link-whatsapp/")
async def link_whatsapp_and_generate_key(data: LinkWhatsAppRequest):
    phone_clean = data.phone.strip().replace(" ", "").replace("-", "")
    biz_name_clean = data.bizName.strip().upper().replace(" ", "")
    
    if not phone_clean or len(phone_clean) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    random_id = random.randint(1000, 9900)
    secret_key = f"KEY-{biz_name_clean or 'BIZ'}-{random_id}"
    
    try:
        user_ref = db.collection("users").document(secret_key)
        user_ref.set({
            "uid": secret_key,
            "whatsapp_phone": phone_clean,
            "business_name": data.bizName,
            "category": data.bizCategory,
            "knowledge_base": data.bizProducts,
            "ai_tone": data.aiTone,
            "ai_lang": data.aiLang,
            "human_takeover": False,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        
        return {
            "status": "success",
            "secretKey": secret_key,
            "linkedPhone": phone_clean
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))