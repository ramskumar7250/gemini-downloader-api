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
    "project_id": "YOUR_PROJECT_ID",  # अपना प्रोजेक्ट आईडी यहाँ डालें
    "private_key_id": "YOUR_PRIVATE_KEY_ID", # अपनी प्राइवेट की आईडी डालें
    "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_ACTUAL_PRIVATE_KEY\n-----END PRIVATE KEY-----\n", # पूरी प्राइवेट की यहाँ डालें (\n के साथ)
    "client_email": "YOUR_CLIENT_EMAIL", # अपना क्लाइंट ईमेल डालें
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