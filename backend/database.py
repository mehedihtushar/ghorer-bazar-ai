import pyodbc
import os
import logging
from dotenv import load_dotenv

# এনভায়রনমেন্ট ভেরিয়েবল লোড করা
load_dotenv()

# লগিং সেটআপ (যাতে এরর হলে টার্মিনালে বিস্তারিত দেখা যায়)
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
            timeout=10  # ১০ সেকেন্ড পর্যন্ত অপেক্ষা করবে
        )
        return conn
    except Exception as e:
        logger.error(f"❌ ডাটাবেস কানেকশন এরর: {e}")
        return None

def fetch_context(query: str) -> str:
    """ইউজারের প্রশ্নের ওপর ভিত্তি করে ডাটাবেস থেকে বিস্তারিত কনটেক্সট নিয়ে আসা।"""
    if not query or len(query.strip()) < 2:
        return "সঠিকভাবে প্রশ্ন করুন যাতে আমি তথ্য খুঁজে পাই।"

    ctx = []
    conn = get_connection()
    
    if not conn:
        return "দুঃখিত, বর্তমানে ডাটাবেস সার্ভারের সাথে সংযোগ বিচ্ছিন্ন। অনুগ্রহ করে কিছুক্ষণ পর চেষ্টা করুন।"

    try:
        cursor = conn.cursor()
        search_term = f'%{query}%'

        # --- ১. পণ্য তথ্য (TOP 5) ---
        # গ্রাহক যখন কোনো পণ্যের নাম বা ক্যাটাগরি জানতে চায়
        cursor.execute("""
            SELECT TOP 5 product_name, category, price, stock_quantity, unit
            FROM Products 
            WHERE product_name LIKE ? OR category LIKE ?
        """, (search_term, search_term))
        products = cursor.fetchall()
        if products:
            ctx.append("🛍️ সংশ্লিষ্ট পণ্যের তালিকা:")
            for p in products:
                status = "স্টক আছে" if p[3] > 0 else "বর্তমানে স্টকে নেই"
                ctx.append(f"- {p[0]} ({p[1]}): দাম {p[2]} টাকা, {status} (পরিমাণ: {p[3]} {p[4]})")

        # --- ২. অর্ডার ও ডেলিভারি তথ্য (TOP 2 - লেটেস্ট তথ্য আগে) ---
        # আইডি বা ফোন নম্বর দিয়ে সার্চ
        cursor.execute("""
            SELECT TOP 2 O.order_id, O.order_status, O.payment_status, O.total_amount,
                         D.delivery_status, D.delivery_area, D.assigned_rider, 
                         D.estimated_delivery_time, C.full_name
            FROM Orders O
            LEFT JOIN Delivery D ON O.order_id = D.order_id
            LEFT JOIN Customers C ON O.customer_id = C.customer_id
            WHERE CAST(O.order_id AS NVARCHAR) LIKE ? OR C.phone_number LIKE ?
            ORDER BY O.order_id DESC
        """, (search_term, search_term))
        orders = cursor.fetchall()
        if orders:
            ctx.append("\n📦 অর্ডারের বর্তমান অবস্থা:")
            for row in orders:
                ctx.append(
                    f"- আইডি: {row[0]} | কাস্টমার: {row[8]} | স্ট্যাটাস: {row[1]} | "
                    f"পেমেন্ট: {row[2]} | মোট: {row[3]} টাকা | "
                    f"ডেলিভারি: {row[4]} (এলাকা: {row[5]}, রাইডার: {row[6]}) | "
                    f"সম্ভাব্য সময়: {row[7]}"
                )

        # --- ৩. FAQ ও পলিসি (TOP 5) ---
        # সাধারণ প্রশ্নের উত্তর দেওয়ার জন্য
        cursor.execute("""
            SELECT TOP 5 question, answer 
            FROM FAQ 
            WHERE question LIKE ? OR answer LIKE ? OR category LIKE ?
        """, (search_term, search_term, search_term))
        faqs = cursor.fetchall()
        if faqs:
            ctx.append("\n❓ সাধারণ জিজ্ঞাসা (FAQ):")
            for f in faqs:
                ctx.append(f"- প্রশ্ন: {f[0]} | উত্তর: {f[1]}")

        # --- ৪. পেমেন্ট তথ্য (TOP 1) ---
        cursor.execute("""
            SELECT TOP 1 transaction_id, payment_method, amount_paid, payment_date
            FROM Payments WHERE transaction_id LIKE ? OR order_id LIKE ?
        """, (search_term, search_term))
        pay = cursor.fetchone()
        if pay:
            ctx.append(f"\n💳 পেমেন্ট রেকর্ড → আইডি: {pay[0]}, মাধ্যম: {pay[1]}, পরিমাণ: {pay[2]} টাকা, তারিখ: {pay[3]}")

        # --- ৫. অভিযোগ ও সমস্যা (TOP 2) ---
        cursor.execute("""
            SELECT TOP 2 issue_type, status, created_at 
            FROM Complaints WHERE description LIKE ? OR order_id LIKE ?
        """, (search_term, search_term))
        complaints = cursor.fetchall()
        if complaints:
            ctx.append("\n⚠️ অভিযোগ সংক্রান্ত তথ্য:")
            for c in complaints:
                ctx.append(f"- ধরন: {c[0]}, স্ট্যাটাস: {c[1]}, তারিখ: {c[2]}")

        # --- ৬. প্রোমো কোড ও অফার (TOP 2) ---
        cursor.execute("""
            SELECT TOP 2 promo_code, discount_percent, expiry_date 
            FROM Promotions 
            WHERE is_active = 1 AND expiry_date >= CAST(GETDATE() AS DATE)
            AND (promo_code LIKE ? OR category_applicable LIKE ?)
        """, (search_term, search_term))
        promos = cursor.fetchall()
        if promos:
            ctx.append("\n🎁 চলমান অফার:")
            for pr in promos:
                ctx.append(f"- কোড: {pr[0]}, ছাড়: {pr[1]}%, মেয়াদ: {pr[2]}")

    except pyodbc.Error as e:
        logger.error(f"❌ কুয়েরি এরর: {e}")
        return "তথ্য খোঁজার সময় একটি কারিগরি সমস্যা হয়েছে।"
    
    finally:
        if conn:
            conn.close() # কাজ শেষে কানেকশন অবশ্যই বন্ধ করা হচ্ছে

    # সব ডেটা একসাথে করে টেক্সট আকারে পাঠানো
    if not ctx:
        return "দুঃখিত, আপনার প্রশ্নের সাথে মিল আছে এমন কোনো তথ্য আমাদের ডাটাবেসে পাওয়া যায়নি।"
    
    return "\n".join(ctx)