from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from rag_engine import generate_smart_response

app = FastAPI()

# মোবাইল থেকে এক্সেস করার জন্য CORS অবশ্যই লাগবে
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# আপনার HTML ফাইলের সঠিক ফুল পাথ (r দিয়ে শুরু করবেন)
FILE_PATH = r"E:/CustomreCallAgentSoftware/frontend/ghorer_bazar_chatbot.html"

class ChatMsg(BaseModel):
    message: str

# ১. হোম রুট (মোবাইল থেকে লিঙ্কে ঢুকলে এই ফাইলটি ওপেন হবে)
@app.get("/", response_class=HTMLResponse)
async def index():
    try:
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            return HTMLResponse(content=f"Error: File not found at {FILE_PATH}", status_code=404)
    except Exception as e:
        return HTMLResponse(content=f"Server Error: {str(e)}", status_code=500)

# ২. চ্যাট এন্ডপয়েন্ট
@app.post("/chat")
async def chat(data: ChatMsg):
    try:
        print(f"User Message: {data.message}")
        reply = generate_smart_response(data.message)
        return {"reply": reply}
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return JSONResponse(status_code=500, content={"reply": "এআই সার্ভারে সমস্যা হচ্ছে।"})

if __name__ == "__main__":
    # host="0.0.0.0" ই মোবাইল থেকে ঢোকার চাবিকাঠি
    uvicorn.run(app, host="0.0.0.0", port=8080)