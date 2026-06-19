from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import re

app = FastAPI()

# CORS इनेबल करना ताकि Framer वेबसाइट इस बैकएंड से बात कर सके
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

# Render के Environment Variables से आपकी फ्री API Key उठाएगा
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

@app.post("/get-video/")
async def get_video_link(data: VideoRequest):
    input_url = data.url.strip()
    
    if not input_url:
        raise HTTPException(status_code=400, detail="URL की जरूरत है")
    
    if "gemini.google.com/share" not in input_url:
        raise HTTPException(status_code=400, detail="यह वैध जेमिनी शेयर लिंक नहीं है।")
        
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="सर्वर एरर: Render पर API Key सेट नहीं की गई है।")
    
    try:
        # 1. जेमिनी शेयर पेज का रॉ सोर्स कोड फेच करना
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        page_res = requests.get(input_url, headers=headers, timeout=10)
        if page_res.status_code != 200:
            raise HTTPException(status_code=500, detail="गूगल सर्वर से पेज लोड नहीं हो सका।")
            
        page_text = page_res.text
        
        # 2. आपकी फ्री Gemini API का इस्तेमाल करके पेज के अंदरूनी डेटा में से असली मीडिया लिंक ढूंढना
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"""
        You are an expert source code parser. Analyze this raw HTML text from a Google Gemini share page and extract the DIRECT, RAW, UNWATERMARKED source URL of the video or image (usually hosted on googlevideo.com or googleusercontent.com). 
        Do not return any explanation, introduction, or markdown format code blocks. Just return the raw URL string directly. If multiple media links exist, return the highest quality one.
        
        HTML Content snippet:
        {page_text[:38000]}
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        api_res = requests.post(api_url, json=payload, timeout=10)
        
        if api_res.status_code == 200:
            result_json = api_res.json()
            extracted_text = result_json['candidates'][0]['content']['parts'][0]['text'].strip()
            
            if "http" in extracted_text:
                clean_url = extracted_text.split('\n')[0].replace('`', '').strip()
                return {"status": "success", "download_url": clean_url}
        
        # बैकअप तरीका: अगर किसी वजह से API रिस्पॉन्स नहीं देती तो पुराना Regex काम करेगा
        backup_match = re.search(r'(https://[^\s"\',\\]+googlevideo\.com/[^\s"\',\\]*)', page_text)
        if backup_match:
            return {"status": "success", "download_url": backup_match.group(1).replace('\\u003d', '=').replace('\\', '')}
            
        raise HTTPException(status_code=400, detail="बिना वॉटरमार्क वाली असली फ़ाइल का लिंक नहीं मिल सका।")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"सर्वर एरर: {str(e)}")