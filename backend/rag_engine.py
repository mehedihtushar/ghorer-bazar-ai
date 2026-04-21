import google.generativeai as genai
from datetime import datetime
from database import fetch_context

# ১. কনফিগারেশন
API_KEY = "AIzaSyDu_0CpCTZk3p4zGxc7S3YObChm4xHxlaI"

# সিস্টেম ইন্সট্রাকশন: এটি এআই-এর ব্যক্তিত্ব নির্ধারণ করবে
SYSTEM_INSTRUCTION = """
আপনি 'ঘরের বাজার' (Ghorer Bazar) এর একজন অত্যন্ত দক্ষ, বন্ধুসুলভ এবং বুদ্ধিমান কাস্টমার সাপোর্ট এক্সিকিউটিভ।

আপনার কথা বলার নিয়মাবলী:
১. গ্রাহক যদি শুভেচ্ছা বিনিময় (হাই, হ্যালো, কেমন আছেন) বা সাধারণ কথা বলে, তবে বন্ধুসুলভ উত্তর দিন। সরাসরি মোবাইল নম্বর চাইবেন না।
২. যদি গ্রাহক নির্দিষ্ট কোনো অর্ডার, ডেলিভারি বা প্রোডাক্ট নিয়ে সমস্যা বলে এবং আপনার কাছে থাকা 'তথ্য' (Data) সেকশনে তার উত্তর না থাকে, শুধুমাত্র তখনই বিনীতভাবে তার রেজিস্টার্ড মোবাইল নম্বর বা অর্ডার আইডিটি চাইবেন।
৩. উত্তর সবসময় শুদ্ধ বাংলায়, ছোট এবং পেশাদার হতে হবে।
৪. ডাটাবেজে তথ্য থাকলে সেটাকে সহজভাবে বুঝিয়ে বলুন। নিজের থেকে কোনো মিথ্যা তথ্য বা অফার দেবেন না।
৫. 'বালা আসোনি' বা এই জাতীয় ক্যাজুয়াল কথার ক্ষেত্রে স্মার্টলি উত্তর দিন (যেমন: 'জি, আমি আপনার কথাটি ঠিক বুঝতে পারিনি, তবে আমি আপনাকে ঘরের বাজারের পণ্য বা অর্ডার নিয়ে সাহায্য করতে পারি')।
"""

def generate_smart_response(user_input):
    try:
        # ২. ডাটাবেজ থেকে প্রাসঙ্গিক তথ্য সংগ্রহ
        db_context = fetch_context(user_input)
        current_time = datetime.now().strftime("%I:%M %p")
        
        # ৩. এপিআই কনফিগারেশন
        genai.configure(api_key=API_KEY)
        
        # ৪. মডেল সিলেকশন (Gemini 1.5 Flash সবচেয়ে সাশ্রয়ী এবং স্থিতিশীল)
        # যদি আপনার অ্যাকাউন্টে ২.০ কাজ করে, তবে 'gemini-2.0-flash' ব্যবহার করতে পারেন।
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # ৫. স্মার্ট জেনারেশন কনফিগ (টোকেন বাঁচানোর জন্য)
        generation_config = {
            "temperature": 0.5,       # কিছুটা ক্রিয়েটিভিটি থাকবে যাতে রোবটের মতো না শোনায়
            "max_output_tokens": 200, # উত্তর ছোট রাখতে টোকেন লিমিট
            "top_p": 0.9,
        }

        # ৬. প্রম্পট ডিজাইন
        user_prompt = f"""
        বর্তমান সময়: {current_time}
        ডাটাবেজ থেকে পাওয়া তথ্য: {db_context}
        গ্রাহকের প্রশ্ন: {user_input}
        
        উত্তর:"""

        # ৭. রেসপন্স জেনারেট
        response = model.generate_content(
            user_prompt,
            generation_config=generation_config
        )
        
        if response and response.text:
            return response.text.strip()
        else:
            return "দুঃখিত, আমি আপনার কথাটি বুঝতে পারছি না। দয়া করে বিস্তারিত বলুন।"

    except Exception as e:
        error_msg = str(e)
        # ইউজারকে সরাসরি টেকনিক্যাল এরর না দেখিয়ে সুন্দর মেসেজ দেওয়া
        if "API_KEY_INVALID" in error_msg or "expired" in error_msg:
            return "সিস্টেম আপডেট চলছে (Invalid API Key)। দয়া করে কিছুক্ষণ পর চেষ্টা করুন।"
        elif "quota" in error_msg.lower():
            return "দুঃখিত, বর্তমানে অনেক বেশি ট্রাফিক। দয়া করে ১ মিনিট পর আবার মেসেজ দিন।"
        
        print(f"Debug Log: {error_msg}")
        return "কারিগরি সমস্যার কারণে উত্তর দিতে পারছি না। আমাদের হেল্পলাইনে কল করুন।"