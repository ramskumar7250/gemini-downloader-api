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

# 1. चाबी को बिना किसी न्यूलाइन (\n) के एक सिंगल लाइन में रख दिया है, ताकि रेंडर इसे कभी रिजेक्ट न कर पाए
RAW_KEY = (
    "-----BEGIN PRIVATE KEY-----\n"
    "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCKBgQDWKNCIP/S\n"
    "kdxhrY2PHrUq8uApUAhQRWnYG\n"
    "/iDFCOx2lXjzNaz4qD2jI/To6oUyhy22Te3w\n"
    "RbR4u0Acg7FP3feH8lvmYny5wu/C\n"
    "dJghlRBxP9R1+ZjUU789Zg1NLa8Jt0didB\n"
    "/yMgLsx0Noys+qVtQDskLFAJSM3a9L\n"
    "kxAZf88kQwKBgHR5GeORDKOwPdokdF7J\n"
    "hdMUGxiUOc0RevtphQIPGLYKkX4ikfS3\n"
    "G9D+mpWYN+yfNBju8gqFfLgUJOnbHuhT\n"
    "/PuNuZdb+a0VUir93TSOzcrKaR32KzWE\n"
    "5dYEPfHgLazo//33Hcjhq9+h7eOkDw6A\n"
    "0mZhqOO7sobc41PcvxJb+jQBAoGAOvDO\n"
    "u8EGXsFcWinni0wZVqk8RnSv+zqvYytL\n"
    "746OLfDjceRi76i2FhFOVVA+SnLD1PnL\n"
    "s6YrjlLSyUZBZZ7MgoDkZBrVAvcwr48R\n"
    "U6TH+rM7kSCZvE40Qvy0Snp5Qy5LGkCl\n"
    "ji3PekU5Oz0ePF5bSY0lLT0EpWRZ223l\n"
    "L29qnisCgYEAoHfP6+JreU3bWlCqR7Qz\n"
    "twu0fy70NKo1TpMUfxZyK2ITAjwvTiQ\n"
    "/nFHd+ZnGAwgzdJoj0XWcQkW9dOLFbg98\n"
    "/JJ/fMI7bJRgM0/XyCJG8B8J+GNlFYkx\n"
    "Dxg2s4FZrUtfwGFAM1z0aQinJ/FLfsn8\n"
    "xmwxw41gB865uSVp4s3py4o=\n"
    "-----END PRIVATE KEY-----\n"
)

firebase_config = {
    "type": "service_account",
    "project_id": "marva-8280e",
    "private_key_id": "d62c417a35e8a4b59e57fbbce13972be7bd66658",
    "private_key": RAW_KEY,
    "client_email": "firebase-adminsdk-fbsvc@marva-8280e.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token"
}

# फायरबेस इनिशियलाइज़ेशन
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        print("Firebase successfully initialized!")
except Exception as e:
    print(f"Firebase Init Critical Error: {str(e)}")

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

class TakeoverRequest(BaseModel):
    uid: str
    takeover: bool

@app.post("/train-ai/")
async def train_ai_core(data: TrainRequest):
    return {"status": "success", "message": "Local sync complete"}

@app.post("/link-whatsapp/")
async def link_whatsapp_and_generate_key(data: LinkWhatsAppRequest):
    phone_clean = data.phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    biz_name_clean = data.bizName.strip().upper().replace(" ", "")
    
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
            "metrics_count": 148
        })
        return {"status": "success", "secretKey": secret_key, "linkedPhone": phone_clean}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-dashboard/{uid}")
async def get_dashboard_data(uid: str):
    try:
        user_doc = db.collection("users").document(uid).get()
        if user_doc.exists:
            return user_doc.to_dict()
        else:
            raise HTTPException(status_code=404, detail="Token not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/toggle-takeover/")
async def toggle_human_takeover(data: TakeoverRequest):
    try:
        user_ref = db.collection("users").document(data.uid)
        user_ref.update({"human_takeover": data.takeover})
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))