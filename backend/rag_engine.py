import os
import sys
import json
from datetime import datetime

# ১. পাইথন পাথ ফিক্স
site_packages_path = r'C:\Users\user\AppData\Local\Programs\Python\Python310\lib\site-packages'
if site_packages_path not in sys.path:
    sys.path.append(site_packages_path)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

# database.py থেকে সংশোধিত fetch_context ইমপোর্ট
try:
    from database import fetch_context
except ImportError:
    print("Error: database.py file or fetch_context function not found!")

# ২. কনফিগারেশন
<<<<<<< HEAD
API_KEY = "AIzaSyCeMJxPPAJO_fN1pkAZ5p0T-8_3sgzVNSY" 
=======
API_KEY = "AIzaSyDcSO_Tytl83tL1VFdEMdb01esLfw8Lp98" 
>>>>>>> ab588a589dff18f01e24937a05e3ea3fffa53ea1

# ৩. মডেল সেটআপ
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=API_KEY,
    temperature=0.3 # একটু কমানো হয়েছে যাতে সে ডাটা নিয়ে ফ্যান্টাসি না করে রিয়েল উত্তর দেয়
)

# ৪. মেমোরি স্টোর
store = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    history = store[session_id]
    if len(history.messages) > 15:
        history.messages = history.messages[-15:]
    return history

# ৫. প্রম্পট টেমপ্লেট (পুরোপুরি পরিবর্তন করা হয়েছে)
# এখানে জেমিনাইকে 'মাস্টার মাইন্ড' হিসেবে গাইড করা হয়েছে
system_instruction = """
আপনি 'ঘরের বাজার' (Ghorer Bazar) এর একজন অতি বুদ্ধিমান সেলস এবং কাস্টমার সাপোর্ট এজেন্ট। 

আপনার কাজের ধরন:
১. নিচে 'Context (Data Source)' সেকশনে আমাদের দোকানের সব পণ্যের তালিকা, দাম, ওজন এবং পলিসি দেওয়া আছে।
২. কাস্টমার যদি ইংরেজিতে (যেমন: modhu, koto kg, dam) প্রশ্ন করে, আপনি Context থেকে তার বাংলা প্রতিশব্দ (মধু, ওজন, দাম) নিজে বুঝে নিয়ে উত্তর দিবেন।
৩. যদি কাস্টমার কোনো পণ্যের ভেরিয়েশন বা ওজন জানতে চায়, আপনি Context থেকে ওই পণ্যের সবকটি ভেরিয়েশন (যেমন: ২৫০ গ্রাম, ৫০০ গ্রাম, ১ কেজি) সুন্দর করে লিস্ট আকারে বলবেন।
৪. কাস্টমারকে কখনোই বলবেন না যে 'তথ্য নেই'—যদি Context-এ ওই পণ্য সম্পর্কিত সামান্য তথ্যও থাকে। 
৫. আপনার উত্তর হবে বন্ধুত্বপূর্ণ, শুদ্ধ বাংলায় এবং কাস্টমারকে কেনাকাটায় উৎসাহিত করার মতো।

Context (Data Source): 
{context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_instruction),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{user_input}"),
])

# ৬. চেইন তৈরি
chain = prompt | llm

chat_chain = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="user_input",
    history_messages_key="chat_history",
)

# ৭. মেইন ফাংশন (Smart Intelligence-First RAG)
def generate_smart_response(user_input: str, session_id: str = "default") -> str:
    """
    এই ফাংশনটি এখন সরাসরি ডাটাবেস থেকে সব নলেজ নিয়ে এসে জেমিনাইকে দিবে।
    """
    print(f"--- Processing Input: {user_input} ---")

    # ধাপ ১: ডাটাবেস থেকে সব 'Raw Data' সংগ্রহ করা
    # আমরা এখন আর কুয়েরি ম্যাচ করার জন্য অপেক্ষা করবো না, সব ডাটা নিয়ে আসবো
    try:
        # এখানে database.py এর নতুন fetch_context কাজ করবে যা সব ডাটা দেয়
        db_context, similarity_score = fetch_context(user_input)
    except Exception as e:
        print(f"--- DB Fetch Error: {e} ---")
        db_context = "Database currently unavailable. Answer based on general knowledge."
        similarity_score = 0.0

    # ধাপ ২: জেমিনাই দিয়ে উত্তর তৈরি করা
    try:
        # জেমিনাই এখন তার চোখের সামনে পুরো প্রোডাক্ট লিস্ট এবং FAQ দেখতে পাবে
        # তাই সে নিজেই 'modhu' মানে 'মধু' সেটা বুঝে উত্তর দিবে।
        response = chat_chain.invoke(
            {
                "user_input": user_input,
                "context": db_context,
            },
            config={"configurable": {"session_id": session_id}},
        )
        
        return response.content.strip()

    except Exception as e:
        print(f"--- AI Generation Error: {str(e)} ---")
        return "সম্মানিত গ্রাহক, দুঃখিত যে এই মুহূর্তে উত্তর দিতে কিছুটা সমস্যা হচ্ছে। দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।"

# ৮. টেস্ট রান
if __name__ == "__main__":
    print("Ghorer Bazar AI Agent is running... (Type 'exit' to stop)")
    while True:
        text = input("Customer: ")
        if text.lower() == 'exit': break
        print("AI:", generate_smart_response(text))