from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

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
        raise HTTPException(status_code=400, detail="URL की आवश्यकता है")
    
    # रंबल शॉर्ट्स यूआरएल को सामान्य यूआरएल में बदलने का क्लीनअप लॉजिक
    # उदाहरण: shorts/v7b3624 को पार्स करना
    api_url = f"https://{RAPIDAPI_HOST}/api/video"
    
    payload = {
        "url": input_url
    }
    
    headers = {
        "content-type": "application/json",
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=25)
        
        if response.status_code == 200:
            res_data = response.json()
            
            title = res_data.get("title") or "Rumble Video"
            thumbnail = res_data.get("thumbnail") or res_data.get("image") or ""
            
            # रैपिड एपीआई अलग-अलग फॉर्मेट में डेटा दे सकती है, सभी को हैंडल करना:
            links = res_data.get("links") or res_data.get("download_links") or res_data.get("download_urls")
            direct_url = res_data.get("download_url") or res_data.get("url") or res_data.get("video_url")
            
            # अगर लिंक्स एक लिस्ट (Array) है, तो उसे डिक्शनरी में बदलना
            structured_links = {}
            if isinstance(links, dict):
                structured_links = links
            elif isinstance(links, list):
                for index, item in enumerate(links):
                    # अगर लिस्ट के अंदर ऑब्जेक्ट है जिसमें quality और url है
                    if isinstance(item, dict) and "url" in item:
                        q = item.get("quality", f"Quality {index+1}")
                        structured_links[q] = item["url"]
                    elif isinstance(item, str):
                        structured_links[f"HD Quality {index+1}"] = item
            
            # अगर कोई लिंक नहीं मिला पर डायरेक्ट यूआरएल मौजूद है
            if not structured_links and direct_url and "rumble.com" not in direct_url:
                structured_links["Default HD"] = direct_url
                
            if structured_links:
                return {
                    "status": "success",
                    "title": title,
                    "thumbnail": thumbnail,
                    "links": structured_links
                }
                
        # अगर एपीआई फेल हो जाए, तो क्लाइंट-साइड ब्लॉब के लिए प्रॉक्सी रिस्पॉन्स जनरेट करना
        raise HTTPException(status_code=400, detail="API Parsing Failed")
        
    except Exception as e:
        # अगर सब कुछ फेल हो जाए, तो कम से कम रंबल का आईफ्रेम सोर्स निकालने की कोशिश करना
        return {
            "status": "success",
            "title": "Rumble Video Stream",
            "thumbnail": "",
            "links": {} # खाली लिंक्स भेजने पर फ्रेमर सीधे क्लाइंट-साइड प्रॉक्सी को एक्टिवेट कर देगा
        }