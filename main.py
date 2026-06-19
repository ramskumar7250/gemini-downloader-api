from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import re
import json

app = FastAPI()

# CORS इनेबल करना ताकि आपकी Framer वेबसाइट बिना किसी रुकावट के बात कर सके
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
        response = requests.get(input_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Rumble सर्वर से पेज लोड नहीं हो सका।")
            
        page_source = response.text
        
        # रंबल के अंदर छिपे हुए असली MP4 वीडियो ऑब्जेक्ट को ढूंढना
        embed_match = re.search(r'"embedUrl"\s*:\s*"([^"]+)"', page_source)
        
        if not embed_match:
            # दूसरा पैटर्न: अगर पहले वाले से न मिले
            embed_match = re.search(r'https://rumble\.com/embed/[a-zA-Z0-9_-]+', page_source)
            
        if embed_match:
            embed_url = embed_match.group(1) if hasattr(embed_match, 'group') and len(embed_match.groups()) > 0 else embed_match.group(0)
            if not embed_url.startswith("http"):
                embed_url = "https:" + embed_url
                
            # एम्बेड पेज से असली वीडियो की HD/SD फाइलें निकालना
            embed_res = requests.get(embed_url, headers=headers, timeout=10)
            if embed_res.status_code == 200:
                # वीडियो फाइलों का JSON ब्लॉक खोजना
                video_data_match = re.search(r'"ua"\s*:\s*({.*?})', embed_res.text)
                if video_data_match:
                    video_json = json.loads(video_data_match.group(1))
                    
                    # सबसे बेस्ट क्वालिटी (mp4) का लिंक चुनना
                    available_qualities = ['mp4', 'webm']
                    for q in available_qualities:
                        if q in video_json and len(video_json[q]) > 0:
                            # अलग-अलग रेजोल्यूशन (जैसे 720p, 1080p) में से सबसे पहला (High Quality) चुनना
                            resolutions = list(video_json[q].keys())
                            if resolutions:
                                best_res = resolutions[-1] # आमतौर पर आखिरी वाला सबसे हाई होता है
                                final_video_url = video_json[q][best_res]['url']
                                return {"status": "success", "download_url": final_video_url}

        # बैकअप Regex तरीका
        backup_match = re.search(r'https://[^\s"\']+\.mp4[^\s"\']*', page_source)
        if backup_match:
            return {"status": "success", "download_url": backup_match.group(0)}
            
        raise HTTPException(status_code=400, detail="Rumble वीडियो का डायरेक्ट डाउनलोड लिंक नहीं मिल सका।")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"सर्वर एरर: {str(e)}")