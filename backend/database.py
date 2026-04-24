import pyodbc
import os
import logging
from dotenv import load_dotenv

# এনভায়রনমেন্ট ভেরিয়েবল লোড করা
load_dotenv()

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    """ডাটাবেস কানেকশন তৈরি করার ফাংশন।"""
    try:
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={os.getenv("DB_SERVER")};'
            f'DATABASE={os.getenv("DB_NAME")};'
            f'UID={os.getenv("DB_USER")};'
            f'PWD={os.getenv("DB_PWD")};'
            'TrustServerCertificate=yes;',
            timeout=10
        )
        return conn
    except Exception as e:
        logger.error(f"❌ ডাটাবেস কানেকশন এরর: {e}")
        return None

def fetch_context(query: str, sub_category: str = None) -> tuple:
    """
    ইউজার যাই লিখে পাঠাক না কেন, এটি সংশ্লিষ্ট টেবিল থেকে গুরুত্বপূর্ণ সব ডাটা 
    একত্রে সংগ্রহ করে জেমিনাইকে 'Raw Context' হিসেবে দিবে। 
    """
    conn = get_connection()
    if not conn:
        return "ডাটাবেস সংযোগ বিচ্ছিন্ন।", 0.0

    ctx_blocks = []
    
    try:
        cursor = conn.cursor()

        # ১. প্রোডাক্ট লিস্ট (পুরো লিস্ট তুলে আনা যাতে জেমিনাই নাম ম্যাচ করতে পারে)
        # এখানে কোনো WHERE ক্লজ নেই যাতে ইংরেজি/বাংলা যাই হোক জেমিনাই বুঝতে পারে
        cursor.execute("SELECT product_name, price, unit, stock_quantity, category FROM Products")
        products = cursor.fetchall()
        if products:
            p_list = [f"Product: {p[0]}, Price: {p[1]}, Unit: {p[2]}, Stock: {p[3]}, Category: {p[4]}" for p in products]
            ctx_blocks.append("--- Available Products List ---\n" + "\n".join(p_list))

        # ২. পলিসি ও সাধারণ জিজ্ঞাসা (SubCategories/FAQ)
        # সাব-ক্যাটাগরি নির্দিষ্ট থাকলে সেটা আগে নিবে, নাহলে সব ডিটেইলড কন্টেক্সট
        if sub_category and sub_category != "General":
            cursor.execute("SELECT SubCategoryName, DetailedContext FROM SubCategories WHERE SubCategoryName = ?", (sub_category,))
        else:
            cursor.execute("SELECT SubCategoryName, DetailedContext FROM SubCategories")
            
        faqs = cursor.fetchall()
        if faqs:
            f_list = [f"Topic: {f[0]}, Details: {f[1]}" for f in faqs]
            ctx_blocks.append("\n--- Business Policies & FAQs ---\n" + "\n".join(f_list))

        # ৩. অর্ডার সংক্রান্ত (যদি কুয়েরিতে নাম্বার থাকে তবেই এটি কাজ করবে)
        if any(char.isdigit() for char in query):
            cursor.execute("""
                SELECT TOP 1 O.order_id, O.order_status, D.delivery_status 
                FROM Orders O LEFT JOIN Delivery D ON O.order_id = D.order_id 
                WHERE CAST(O.order_id AS NVARCHAR) LIKE ? 
                ORDER BY O.order_id DESC
            """, (f'%{query}%',))
            order = cursor.fetchone()
            if order:
                ctx_blocks.append(f"\n--- Order Info ---\nOrder ID: {order[0]}, Status: {order[1]}, Delivery: {order[2]}")

    except Exception as e:
        logger.error(f"❌ ডাটাবেস এরর: {e}")
        return "তথ্য সংগ্রহে সমস্যা হয়েছে।", 0.0
    finally:
        conn.close()

    # যদি কোনো ডাটা পাওয়া যায়
    if ctx_blocks:
        full_context = "\n\n".join(ctx_blocks)
        # জেমিনাইকে ফুল ডাটা দেওয়া হচ্ছে, তাই স্কোর ১.০ দেওয়া নিরাপদ
        return full_context, 1.0
    
    return "কোনো তথ্য ডাটাবেসে পাওয়া যায়নি।", 0.0