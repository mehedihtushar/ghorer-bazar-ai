import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# ডাইনামিক পাথ সেটআপ করার জন্য
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# এটি backend ফোল্ডার থেকে এক ধাপ পিছিয়ে গিয়ে frontend ফোল্ডারের ফাইলটি ধরবে
FILE_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "frontend", "ghorer_bazar_chatbot.html"))

# আপনার লজিক ইঞ্জিন ইমপোর্ট
try:
    from rag_engine import generate_smart_response
except ImportError:
    # যদি একই ফোল্ডারে থাকে তবে সরাসরি ইমপোর্ট করবে
    import sys
    sys.path.append(BASE_DIR)
    from rag_engine import generate_smart_response

# লগার সেটআপ
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

# HTML কন্টেন্ট মেমোরিতে ক্যাশ করা
cached_html = ""
if os.path.exists(FILE_PATH):
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            cached_html = f.read()
        logger.info(f"✅ Frontend file loaded successfully from: {FILE_PATH}")
    except Exception as e:
        logger.error(f"❌ Error reading frontend file: {e}")
else:
    logger.warning(f"⚠️ Warning: Frontend file not found at {FILE_PATH}")

class ChatMsg(BaseModel):
    message: str = Field(..., min_length=1) 
    session_id: str = "default"

@app.get("/", response_class=HTMLResponse)
async def index():
    # প্রথমে ক্যাশ থেকে চেক করবে
    if cached_html:
        return HTMLResponse(content=cached_html)
    
    # যদি কোনো কারণে ক্যাশ খালি থাকে তবে আবার রিড করার চেষ্টা করবে
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    
    return HTMLResponse(content="<h1>Error: Frontend file not found!</h1><p>Please check your directory structure.</p>", status_code=404)

@app.post("/chat")
async def chat(data: ChatMsg):
    try:
        clean_msg = data.message.strip()
        if not clean_msg:
            return {"reply": "অনুগ্রহ করে আপনার প্রশ্নটি লিখুন।"}

        logger.info(f"[User] session={data.session_id} | msg={clean_msg}")
        
        # আপনার মূল RAG ইঞ্জিন কল
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
    # host="0.0.0.0" পোর্টে রান হবে যাতে লোকাল নেটওয়ার্ক বা ngrok থেকে পাওয়া যায়
    uvicorn.run(app, host="0.0.0.0", port=8080)