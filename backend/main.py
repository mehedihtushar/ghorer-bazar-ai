import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from rag_engine import generate_smart_response

# লগার সেটআপ (এরর ট্র্যাক করার জন্য)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS সেটআপ
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FILE_PATH = r"E:/CustomreCallAgentSoftware/frontend/ghorer_bazar_chatbot.html"

# HTML কন্টেন্ট মেমোরিতে ক্যাশ (Cost & Speed Optimization)
# প্রতিবার ফাইল রিড করলে ডিস্কের ওপর চাপ পড়ে, যা সার্ভারের খরচ বাড়ায়। 
# একবার লোড করে রাখলে রেসপন্স সুপার ফাস্ট হবে।
cached_html = ""
if os.path.exists(FILE_PATH):
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        cached_html = f.read()

class ChatMsg(BaseModel):
    message: str = Field(..., min_length=1) # ফাঁকা মেসেজ এআই-তে পাঠাবে না (Cost Saving)
    session_id: str = "default"

@app.get("/", response_class=HTMLResponse)
async def index():
    if cached_html:
        return HTMLResponse(content=cached_html)
    
    # যদি ক্যাশ খালি থাকে (প্রথমবার বা ফাইল না থাকলে)
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    
    return HTMLResponse(content="<h1>Error: Frontend file not found!</h1>", status_code=404)

@app.post("/chat")
async def chat(data: ChatMsg):
    try:
        # ইনপুট ভ্যালিডেশন (অপ্রয়োজনীয় এআই কল বন্ধ করে টাকা বাঁচাবে)
        clean_msg = data.message.strip()
        if not clean_msg:
            return {"reply": "অনুগ্রহ করে আপনার প্রশ্নটি লিখুন।"}

        logger.info(f"[User] session={data.session_id} | msg={clean_msg}")
        
        # মূল আরএজি ইঞ্জিন কল (আপনার লজিক ঠিক রাখা হয়েছে)
        reply = generate_smart_response(clean_msg, session_id=data.session_id)
        
        return {"reply": reply}

    except Exception as e:
        logger.error(f"[CRITICAL ERROR] {e}")
        return JSONResponse(
            status_code=500, 
            content={"reply": "দুঃখিত, আমাদের সার্ভারে এই মুহূর্তে কিছুটা সমস্যা হচ্ছে। কিছুক্ষণ পর চেষ্টা করুন।"}
        )

@app.get("/health")
async def health():
    return {"status": "ok", "database": "connected"}

if __name__ == "__main__":
    # host="0.0.0.0" এবং port=8080 আপনার ngrok এর জন্য পারফেক্ট
    uvicorn.run(app, host="0.0.0.0", port=8080)