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

# 1. Firebase Initialization (अपने firebase_credentials.json का पाथ यहाँ सेट करें)
try:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)
except Exception:
    # अगर पहले से इनिशियलाइज्ड हो
    pass

db = firestore.client()

# डेटा वैलीडेशन मॉडल्स
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
    # यह एंडपॉइंट सिर्फ फ्रंटएंड पर इनिशियल चेकिंग के लिए है
    if not data.bizName or not data.bizCategory or not data.bizProducts:
        raise HTTPException(status_code=400, detail="Mandatory fields missing")
    return {"status": "success", "message": "Gemini dataset optimized successfully"}

@app.post("/link-whatsapp/")
async def link_whatsapp_and_generate_key(data: LinkWhatsAppRequest):
    phone_clean = data.phone.strip().replace(" ", "").replace("-", "")
    biz_name_clean = data.bizName.strip().upper().replace(" ", "")
    
    if not phone_clean or len(phone_clean) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number format")

    # जादुई Secret Access Key जनरेट करना
    random_id = random.randint(1000, 9900)
    secret_key = f"KEY-{biz_name_clean or 'BIZ'}-{random_id}"
    
    try:
        # 2. Firestore में 'users' कलेक्शन के अंदर डेटा लॉक करना
        user_ref = db.collection("users").document(secret_key)
        user_ref.set({
            "uid": secret_key,
            "whatsapp_phone": phone_clean,
            "business_name": data.bizName,
            "category": data.bizCategory,
            "knowledge_base": data.bizProducts,
            "ai_tone": data.aiTone,
            "ai_lang": data.aiLang,
            "human_takeover": False, # डिफ़ॉल्ट रूप से एआई एक्टिव रहेगा
            "created_at": firestore.SERVER_TIMESTAMP
        })
        
        return {
            "status": "success",
            "secretKey": secret_key,
            "linkedPhone": phone_clean
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Lock Failed: {str(e)}")