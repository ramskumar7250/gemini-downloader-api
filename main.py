from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import re
import urllib.parse

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
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        page_res = requests.get(input_url, headers=headers, timeout=12)
        if page_res.status_code != 200:
            raise HTTPException(status_code=500, detail="गूगल सर्ver से पेज लोड नहीं हो सका।")
            
        page_text = page_res.text
        
        # बैकएंड हैक: पहले पूरे पेज में से WIZ_global_data ब्लॉक को अलग करना ताकि एआई सीधे सही जगह ढूंढे
        wiz_data_match = re.search(r'window\.WIZ_global_data\s*=\s*(\{.*?\});', page_text)
        context_data = wiz_data_match.group(1) if wiz_data_match else page_text[:40000]

        # जेमिनी एआई मॉडल से सीधे कड़े निर्देशों के साथ डायरेक्ट यूआरएल मांगना
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"""
        You are a raw text extraction tool. Your job is to strictly find and extract the direct high-quality video or image URL located inside this Google data structure. Look specifically for fields containing strings with "googlevideo.com" or "googleusercontent.com".
        
        CRITICAL RULES:
        1. Return ONLY the raw URL string (e.g., https://...).
        2. Do NOT wrap it in markdown block codes like ```url.
        3. Do NOT provide any explanation, text, or warnings.
        4. If it contains encoded entities like '\\u003d', decode them to '='.
        
        Data to scan:
        {context_data[:35000]}
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
            
            # क्लीनिंग प्रोसेस
            clean_url = extracted_text.replace('`', '').replace('\\\n', '').strip()
            if "http" in clean_url:
                final_url = clean_url.split('\n')[0].split('"')[0].split("'")[0]
                return {"status": "success", "download_url": final_url}
        
        # सुपर-इम्प्रूव्ड अल्टीमेट बैकअप Regex: अगर एआई कन्फ्यूज हो जाए, तो कोड खुद निकालेगा
        regex_patterns = [
            r'(https://[^\s"\',\\]+googlevideo\.com/[^\s"\',\\]*)',
            r'(https://[^\s"\',\\]+googleusercontent\.com/[^\s"\',\\]*)'
        ]
        
        for pattern in regex_patterns:
            matches = re.findall(pattern, page_text)
            for match in matches:
                decoded_url = match.encode().decode('unicode-escape').replace('\\', '')
                decoded_url = decoded_url.split('"')[0].split("'")[0].split(']')[0]
                if "avatar" not in decoded_url and "lh3.googleusercontent" not in decoded_url:
                    return {"status": "success", "download_url": decoded_url}
            
        raise HTTPException(status_code=400, detail="बिना वॉटरमार्क वाली असली फ़ाइल का लिंक नहीं मिल सका।")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"सर्वर एरर: {str(e)}")