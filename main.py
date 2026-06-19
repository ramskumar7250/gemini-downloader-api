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

class MediaRequest(BaseModel):
    url: str

RAPIDAPI_KEY = "a40796553cmsh26d51d82ef613e0p1cfa9ejsn34c5c0c6be3d"

@app.post("/get-video/")
async def remove_gemini_watermark(data: MediaRequest):
    input_url = data.url.strip()
    
    if not input_url:
        raise HTTPException(status_code=400, detail="URL की जरूरत है")
    
    # फिक्स्ड रैपिड-एपीआई एंडपॉइंट यूआरएल (जो 404 को बाईपास करेगा)
    api_url = "https://removebanana.p.rapidapi.com/api/remove-watermark/"
    
    payload = {
        "image": input_url
    }
    
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "x-rapidapi-host": "removebanana.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    
    try:
        response = requests.post(api_url, data=payload, headers=headers, timeout=25)
        
        # अगर ट्रेलिंग स्लैश से भी न मिले तो बिना स्लैश वाला बेस ट्राई करना
        if response.status_code == 404:
            api_url_alt = "https://removebanana.p.rapidapi.com/api/remove-watermark"
            response = requests.post(api_url_alt, data=payload, headers=headers, timeout=25)

        if response.status_code == 200:
            res_data = response.json()
            final_url = res_data.get("converted_url") or res_data.get("url") or res_data.get("download_url")
            
            if final_url:
                return {"status": "success", "download_url": final_url}
            else:
                return {"status": "success", "download_url": input_url}
                
        raise HTTPException(status_code=response.status_code, detail="वाटरमार्क हटाने वाली एपीआई से रिस्पांस नहीं मिला।")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API Connection Error: {str(e)}")