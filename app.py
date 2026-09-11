from flask import Flask, render_template, request, jsonify
import os
import psycopg2

app = Flask(__name__)

def get_db_connection():
    # Kuhaon ang DATABASE_URL gikan sa Render environment variables
    DATABASE_URL = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                gmail VARCHAR(255) PRIMARY KEY,
                password VARCHAR(255),
                gcash_number VARCHAR(50),
                balance REAL DEFAULT 0.0,
                referred_by VARCHAR(255)
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    gmail = data.get('gmail')
    password = data.get('password')
    gcash = data.get('gcash')
    ref_code = data.get('refCode', "").strip()
    
    if not gmail or not password or not gcash:
        return jsonify({"status": "error", "message": "Palihug pun-a ang tanang kinahanglang field!"})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT gmail FROM users WHERE gmail = %s', (gmail,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Ang kini nga Gmail narehistro na daan!"})
        
        cursor.execute('INSERT INTO users (gmail, password, gcash_number, balance, referred_by) VALUES (%s, %s, %s, %s, %s)', 
                       (gmail, password, gcash, 0.0, ref_code))
        
        if ref_code and ref_code != gmail:
            cursor.execute('SELECT gmail FROM users WHERE gmail = %s', (ref_code,))
            if cursor.fetchone():
                cursor.execute('UPDATE users SET balance = balance + 1.0 WHERE gmail = %s', (ref_code,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": "Malamposon ang pagrehistro! Pwede na ka mag-login."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    gmail = data.get('gmail')
    password = data.get('password')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password, gcash_number, balance FROM users WHERE gmail = %s', (gmail,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            return jsonify({"status": "error", "message": "Wala makita ang maong Gmail account."})
        
        db_password, gcash, balance = row[0], row[1], row[2]
        
        if db_password != password:
            return jsonify({"status": "error", "message": "Sayop ang imong password!"})
        
        return jsonify({
            "status": "success", 
            "gcash": gcash, 
            "balance": balance
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/claim-reward', methods=['POST'])
def claim_reward():
    data = request.json
    gmail = data.get('gmail')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + 5.0 WHERE gmail = %s', (gmail,))
        conn.commit()
        
        cursor.execute('SELECT balance FROM users WHERE gmail = %s', (gmail,))
        new_balance = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "balance": new_balance})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/claim-reward', methods=['POST'])
def claim_reward():
    data = request.json
    gmail = data.get('gmail')
    
    if not gmail:
        return jsonify({"status": "error", "message": "Walay nakit-ang Gmail account."})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # I-update ang balanse
        cursor.execute('UPDATE users SET balance = balance + 5.0 WHERE gmail = %s', (gmail,))
        conn.commit()
        
        # Kuhaon ang bag-ong balanse nga naay check kung naay nakuha
        cursor.execute('SELECT balance FROM users WHERE gmail = %s', (gmail,))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Wala makita ang user sa database."})
            
        new_balance = row[0]
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "balance": new_balance})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})