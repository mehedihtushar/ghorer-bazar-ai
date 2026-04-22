import os
import sys
from datetime import datetime

# ১. পাইথন পাথ ফিক্স
site_packages_path = r'C:\Users\user\AppData\Local\Programs\Python\Python310\lib\site-packages'
if site_packages_path not in sys.path:
    sys.path.append(site_packages_path)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from database import fetch_context

# ২. কনফিগারেশন (আপনার দেওয়া কি-ই থাকবে)
API_KEY = "AIzaSyDle2_vMD891YLm-U9Yh_jTVqHYbdlTvcU"

# ৩. মডেল সেটআপ (হুবহু রাখা হয়েছে)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=API_KEY,
    temperature=0.5
)

# ৪. মেমোরি স্টোর (session-based)
store = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    # শেষ ২০টি মেসেজ রাখো (k=20)
    history = store[session_id]
    if len(history.messages) > 20:
        history.messages = history.messages[-20:]
    return history

# ৫. প্রম্পট টেমপ্লেট (শুধু সিস্টেম ইনস্ট্রাকশন একটু ডিটেইল করা হয়েছে যাতে আউটপুট স্মার্ট হয়)
prompt = ChatPromptTemplate.from_messages([
    ("system", """আপনি 'ঘরের বাজার' (Ghorer Bazar) এর একজন দক্ষ এবং বুদ্ধিমান এআই সাপোর্ট এজেন্ট।

নিয়মাবলী:
- গ্রাহকের আগের কথাগুলো এবং নতুন তথ্য (Context) মিলিয়ে উত্তর দিন।
- যদি Context-এ অনেকগুলো পণ্যের তথ্য থাকে, তবে সেগুলো পয়েন্ট আকারে বিস্তারিত জানাবেন।
- যদি গ্রাহক 'হ্যাঁ', 'কেন?', 'কত?' এর মতো ছোট কথা বলে, তবে আগের কথার রেশ ধরে উত্তর দিন।
- উত্তর শুদ্ধ বাংলায় হবে এবং তথ্যবহুল হবে।

নতুন তথ্য (DB): {context}"""),
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

# ৭. মেইন ফাংশন
def generate_smart_response(user_input: str, session_id: str = "default") -> str:
    try:
        db_context = fetch_context(user_input)

        response = chat_chain.invoke(
            {
                "user_input": user_input,
                "context": db_context,
            },
            config={"configurable": {"session_id": session_id}},
        )

        return response.content.strip()

    except Exception as e:
        print(f"LangChain Error: {str(e)}")
        return "আমি আপনার কথাটি ঠিক বুঝতে পারছি না। দয়া করে বিস্তারিত বলুন।"