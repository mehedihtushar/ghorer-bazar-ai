import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={os.getenv("DB_SERVER")};'
        f'DATABASE={os.getenv("DB_NAME")};'
        f'UID={os.getenv("DB_USER")};'
        f'PWD={os.getenv("DB_PWD")};'
        'TrustServerCertificate=yes;'
    )

def fetch_context(query):
    ctx = []
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # ১. অর্ডার, কাস্টমার এবং ডেলিভারি জয়েন কুয়েরি
        order_sql = """
            SELECT TOP 1 O.order_id, O.order_status, D.delivery_status, C.full_name 
            FROM Orders O
            LEFT JOIN Delivery D ON O.order_id = D.order_id
            LEFT JOIN Customers C ON O.customer_id = C.customer_id
            WHERE O.order_id LIKE ? OR C.phone_number LIKE ?
        """
        cursor.execute(order_sql, (f'%{query}%', f'%{query}%'))
        row = cursor.fetchone()
        if row:
            ctx.append(f"অর্ডার আইডি: {row[0]}, কাস্টমার: {row[3]}, অর্ডারের অবস্থা: {row[1]}, ডেলিভারি অবস্থা: {row[2]}")

        # ২. প্রোডাক্ট ইনভেন্টরি চেক
        cursor.execute("SELECT TOP 1 product_name, price, stock_quantity FROM Products WHERE product_name LIKE ?", (f'%{query}%',))
        p = cursor.fetchone()
        if p:
            ctx.append(f"পণ্য: {p[0]}, দাম: {p[1]} টাকা, স্টক আছে: {p[2]} টি।")
            
        # ৩. পেমেন্ট ট্রানজ্যাকশন চেক
        cursor.execute("SELECT TOP 1 transaction_id, payment_method, amount_paid FROM Payments WHERE transaction_id LIKE ?", (f'%{query}%',))
        pay = cursor.fetchone()
        if pay:
            ctx.append(f"ট্রানজ্যাকশন আইডি: {pay[0]}, মাধ্যম: {pay[1]}, পেমেন্ট করা হয়েছে: {pay[2]} টাকা।")

        # ৪. FAQ এবং ফেসবুক কমেন্টস (Unstructured)
        cursor.execute("SELECT answer FROM FAQ WHERE question LIKE ?", (f'%{query}%',))
        faq = cursor.fetchone()
        if faq: ctx.append(f"FAQ উত্তর: {faq[0]}")

        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")
    
    return '\n'.join(ctx) if ctx else "ডাটাবেজে সরাসরি কোনো তথ্য নেই।"