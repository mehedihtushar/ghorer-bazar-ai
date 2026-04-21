import google.generativeai as genai
import os
from database import fetch_context

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

def generate_smart_response(user_input):
    db_info = fetch_context(user_input)
    
    prompt = f"""
    আপনি 'ঘরের বাজার' এর একজন কাস্টমার সাপোর্ট এক্সপার্ট।
    নিচের ডাটাবেজ কন্টেক্সট ব্যবহার করে ইউজারের প্রশ্নের সঠিক উত্তর দিন।
    
    ডাটাবেজ তথ্য:
    {db_info}
    
    ইউজারের প্রশ্ন: {user_input}
    
    নির্দেশনা:
    - উত্তরটি অবশ্যই শুদ্ধ বাংলায় হবে।
    - ডাটা না থাকলে গ্রাহককে বিনয়ের সাথে অর্ডার আইডি বা তার ফোন নম্বর দিতে বলুন।
    - যদি ইউজার পেমেন্ট নিয়ে কিছু বলে, পেমেন্ট টেবিলের তথ্য থাকলে তা জানান।
    """
    
    try:
        res = model.generate_content(prompt)
        return res.text
    except:
        return "দুঃখিত, এআই সার্ভারে সমস্যা হচ্ছে।"