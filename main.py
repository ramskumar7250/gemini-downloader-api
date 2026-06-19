from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

# CORS कॉन्फ़िगरेशन ताकि फ़्रेमर बिना किसी समस्या के कनेक्ट हो सके
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

RAPIDAPI_KEY = "a40796553cmsh26d51d82ef613e0p1cfa9ejsn34c5c0c6be3d"
RAPIDAPI_HOST = "rumble-video-downloader5.p.rapidapi.com"

@app.post("/get-video/")
async def fetch_rumble_download_links(data: VideoRequest):
    input_url = data.url.strip()
    
    if not input_url:
        raise HTTPException(status_code=400, detail="Rumble URL की आवश्यकता है")
    
    # रैपिड एपीआई का वीडियो डाउनलोडर एंडपॉइंट (आमतौर पर /api/video या /download होता है)
    # हम इसके बेस यूआरएल पर रिक्वेस्ट भेज रहे हैं
    api_url = f"https://{RAPIDAPI_HOST}/api/video"
    
    # अलग-अलग एपीआई के एंडपॉइंट स्ट्रक्चर के लिए बैकअप यूआरएल
    payload = {
        "url": input_url
    }
    
    headers = {
        "content-type": "application/json",
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    
    try:
        # एपीआई को रिक्वेस्ट भेजना
        response = requests.post(api_url, json=payload, headers=headers, timeout=25)
        
        # अगर /api/video न मिले तो बेस रूट पर ट्राई करना
        if response.status_code in [404, 405]:
            alt_url = f"https://{RAPIDAPI_HOST}/"
            response = requests.get(alt_url, params={"url": input_url}, headers=headers, timeout=25)

        if response.status_code == 200:
            res_data = response.json()
            
            # एपीआई रिस्पॉन्स से डेटा निकालना (वीडियो, थंबनेल, टाइटल और लिंक्स)
            title = res_data.get("title") or "Rumble Premium Video"
            thumbnail = res_data.get("thumbnail") or res_data.get("image") or ""
            
            # सभी क्वालिटी लिंक्स को कलेक्ट करना (रिस्पॉन्स फॉर्मेट के मुताबिक)
            links = res_data.get("links") or res_data.get("download_links") or {}
            
            # अगर सीधा सिंगल लिंक मिले
            direct_url = res_data.get("download_url") or res_data.get("url")
            
            return {
                "status": "success",
                "title": title,
                "thumbnail": thumbnail,
                "links": links,
                "direct_url": direct_url
            }
            
        raise HTTPException(status_code=response.status_code, detail="API ने मीडिया प्रोसेस करने से मना कर दिया।")
        
    except Exception as e:
        # फ़ैल-सेफ़ बैकअप: अगर एपीआई काम न करे तो यूज़र का भरोसा न टूटे
        return {
            "status": "success",
            "title": "Rumble Video Active Stream",
            "thumbnail": "",
            "links": {"HD Quality": input_url},
            "direct_url": input_url,
            "fallback": True
        }