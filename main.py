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

class AIChatRequest(BaseModel):
    provider: str  # User select karega: openai, anthropic, ya gemini
    model: str     # User select karega model id
    prompt: str    # User ka sawal

RAPIDAPI_KEY = "a40796553cmsh26d51d82ef613e0p1cfa9ejsn34c5c0c6be3d"

@app.post("/get-video/") # Endpoint purana hi rakh rahe hain taaki Framer me dikkat na ho
async def route_ai_chat(data: AIChatRequest):
    provider = data.provider.strip().lower()
    model = data.model.strip().lower()
    prompt = data.prompt.strip()
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt ki jarurat hai")
    
    # AI Router API ka official endpoint
    api_url = "https://ai-router-api.p.rapidapi.com/chat"
    
    # Strict API format jaisa tumne details me bheja tha
    payload = {
        "provider": provider,
        "model": model,
        "messages": [
            { "role": "user", "content": prompt }
        ]
    }
    
    headers = {
        "content-type": "application/json",
        "x-rapidapi-host": "ai-router-api.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            res_data = response.json()
            # API ke consistent format se text content nikalna
            ai_response_text = res_data.get("content")
            
            if ai_response_text:
                return {"status": "success", "ai_response": ai_response_text}
            else:
                return {"status": "error", "detail": "API se content nahi mil paya."}
                
        raise HTTPException(status_code=response.status_code, detail=f"AI Router Error: {response.text}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Connection Error: {str(e)}")