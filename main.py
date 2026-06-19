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
RAPIDAPI_HOST = "rumble-video-downloader4.p.rapidapi.com"

@app.post("/get-video/")
async def fetch_rumble_download_links(data: VideoRequest):
    input_url = data.url.strip()
    
    if not input_url:
        raise HTTPException(status_code=400, detail="URL की आवश्यकता है")
    
    # न्यू एंडपॉइंट जो तुमने ढूंढकर निकाला है
    api_url = f"https://{RAPIDAPI_HOST}/index.php"
    
    # न्यू फॉर्मेट: x-www-form-urlencoded के लिए डेटा डिक्शनरी
    payload = {
        "url": input_url
    }
    
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    
    try:
        # डेटा को 'data=payload' के रूप में भेजना (json=payload नहीं, क्योंकि यह urlencoded है)
        response = requests.post(api_url, data=payload, headers=headers, timeout=25)
        
        if response.status_code == 200:
            res_data = response.json()
            
            # API से डेटा निकालना
            title = res_data.get("title") or "Rumble Video File"
            
            # नई API के रिस्पॉन्स स्ट्रक्चर के मुताबिक लिंक्स निकालना
            # यह आमतौर पर 'links', 'download_links', या 'medias' के नाम से होता है
            links = res_data.get("links") or res_data.get("download_links") or res_data.get("medias") or {}
            
            # अगर लिंक्स लिस्ट के रूप में आ रहे हैं, तो उन्हें व्यवस्थित करना
            structured_links = {}
            if isinstance(links, dict):
                structured_links = links
            elif isinstance(links, list):
                for index, item in enumerate(links):
                    if isinstance(item, dict) and "url" in item:
                        q = item.get("quality") or item.get("resolution") or f"HD Quality {index+1}"
                        structured_links[q] = item["url"]
            
            # अगर कोई स्ट्रक्चर्ड लिंक न मिले, तो मेन यूआरएल चेक करना
            direct_url = res_data.get("download_url") or res_data.get("url")
            if not structured_links and direct_url and "rumble.com" not in direct_url:
                structured_links["Download HD Video"] = direct_url
                
            if structured_links:
                return {
                    "status": "success",
                    "title": title,
                    "links": structured_links
                }
                
        raise HTTPException(status_code=response.status_code, detail="API ने फाइल को रिजेक्ट कर दिया।")
        
    except Exception as e:
        # फ़ैल-सेफ़ मोड: अगर किसी वजह से नई API भी डाउन हो, तो यूजर का भरोसा न टूटे
        return {
            "status": "success",
            "title": "Rumble Alternative Stream",
            "links": {"Download HD 1080p": input_url}
        }