from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import re
import json

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

@app.post("/get-video/")
async def get_rumble_video(data: VideoRequest):
    input_url = data.url.strip()
    
    if not input_url:
        raise HTTPException(status_code=400, detail="URL की जरूरत है")
    
    if "rumble.com" not in input_url:
        raise HTTPException(status_code=400, detail="Error: केवल वैध Rumble वीडियो लिंक ही सपोर्टेड है।")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        
        # रंबल शॉर्ट्स लिंक को नॉर्मल या एम्बेड फ़ॉर्मेट में बदलने का लॉजिक
        if "/shorts/" in input_url:
            # शॉर्ट्स आईडी निकालना
            shorts_id = input_url.split("/shorts/")[-1].split("?")[0].split("/")[0]
            embed_url = f"https://rumble.com/embed/{shorts_id}/"
        else:
            embed_url = None

        # अगर शॉर्ट्स नहीं है, तो पहले मेन पेज लोड करके एम्बेड यूआरएल ढूँढेंगे
        if not embed_url:
            response = requests.get(input_url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Rumble सर्वर से पेज लोड नहीं हो सका।")
            
            page_source = response.text
            embed_match = re.search(r'"embedUrl"\s*:\s*"([^"]+)"', page_source)
            if not embed_match:
                embed_match = re.search(r'https://rumble\.com/embed/[a-zA-Z0-9_-]+', page_source)
            
            if embed_match:
                embed_url = embed_match.group(1) if hasattr(embed_match, 'group') and len(embed_match.groups()) > 0 else embed_match.group(0)
            else:
                # सीधे वीडियो फ़ाइल खोजने का आख़िरी प्रयास
                backup_match = re.search(r'https://[^\s"\']+\.mp4[^\s"\']*', page_source)
                if backup_match:
                    return {"status": "success", "download_url": backup_match.group(0)}
                raise HTTPException(status_code=400, detail="Rumble एम्बेड लिंक नहीं मिल सका।")

        if embed_url and not embed_url.startswith("http"):
            embed_url = "https:" + embed_url

        # अब सीधे एम्बेड पेज को हिट करके असली HD/SD वीडियो फ़ाइलें निकालना (शॉर्ट्स और लॉन्ग दोनों के लिए)
        embed_res = requests.get(embed_url, headers=headers, timeout=10)
        if embed_res.status_code == 200:
            # एम्बेड कोड में छुपा हुआ "ua" (User Agent/Media Video JSON) ब्लॉक निकालना
            video_data_match = re.search(r'"ua"\s*:\s*({.*?})', embed_res.text)
            if video_data_match:
                video_json = json.loads(video_data_match.group(1))
                
                for q in ['mp4', 'webm']:
                    if q in video_json and len(video_json[q]) > 0:
                        resolutions = list(video_json[q].keys())
                        if resolutions:
                            # सबसे हाई रेजोल्यूशन का असली वीडियो यूआरएल उठाना
                            best_res = resolutions[-1]
                            final_video_url = video_json[q][best_res]['url']
                            return {"status": "success", "download_url": final_video_url}

            # सेकेंडरी बैकअप तरीका एम्बेड पेज के अंदर सीधे mp4 ढूँढना
            direct_mp4 = re.search(r'https://[^\s"\']+\.mp4[^\s"\']*', embed_res.text)
            if direct_mp4:
                return {"status": "success", "download_url": direct_mp4.group(0)}
                
        raise HTTPException(status_code=400, detail="Rumble वीडियो का डायरेक्ट डाउनलोड लिंक नहीं मिल सका।")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rumble सर्वर से पेज लोड नहीं हो सका।")