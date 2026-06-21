from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# रेंडर की सेटिंग (Environment) से पूरी JSON स्ट्रिंग उठाना
firebase_json_env = os.environ.get("FIREBASE_JSON_DATA", "")

try:
    if not firebase_admin._apps:
        if firebase_json_env:
            # स्ट्रिंग को डिक्शनरी में बदलकर लोड करना
            firebase_config = json.loads(firebase_json_env)
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
            print("Firebase successfully initialized from Environment JSON!")
        else:
            print("CRITICAL: FIREBASE_JSON_DATA variable is totally empty!")
except Exception as e:
    print(f"Firebase Init Critical Error: {str(e)}")

# डेटाबेस क्लाइंट को सुरक्षित रूप से शुरू करना
try:
    db = firestore.client()
except Exception as e:
    db = None
    print(f"Firestore Client Connect Error: {str(e)}")

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
    if db is None:
        raise HTTPException(status_code=500, detail="Database client is not initialized")
        
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
    if db is None:
        raise HTTPException(status_code=500, detail="Database client is not initialized")
        
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
    if db is None:
        raise HTTPException(status_code=500, detail="Database client is not initialized")
        
    try:
        user_ref = db.collection("users").document(data.uid)
        user_ref.update({"human_takeover": data.takeover})
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))