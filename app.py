from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            gmail TEXT PRIMARY KEY,
            password TEXT,
            gcash_number TEXT,
            balance REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

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
    
    if not gmail or not password or not gcash:
        return jsonify({"status": "error", "message": "Palihug pun-a ang tanang field!"})
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Tan-awon kung naay nagamit na ana nga Gmail
    cursor.execute('SELECT gmail FROM users WHERE gmail = ?', (gmail,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"status": "error", "message": "Ang kini nga Gmail narehistro na daan!"})
    
    # I-save ang bag-ong account
    cursor.execute('INSERT INTO users (gmail, password, gcash_number, balance) VALUES (?, ?, ?, ?)', 
                   (gmail, password, gcash, 0.0))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "Malamposon ang pagrehistro! Pwede na ka mag-login."})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    gmail = data.get('gmail')
    password = data.get('password')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password, gcash_number, balance FROM users WHERE gmail = ?', (gmail,))
    row = cursor.fetchone()
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

@app.route('/claim-reward', methods=['POST'])
def claim_reward():
    data = request.json
    gmail = data.get('gmail')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + 5.0 WHERE gmail = ?', (gmail,))
    conn.commit()
    
    cursor.execute('SELECT balance FROM users WHERE gmail = ?', (gmail,))
    new_balance = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({"status": "success", "balance": new_balance})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    gmail = data.get('gmail')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance, gcash_number FROM users WHERE gmail = ?', (gmail,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"status": "error", "message": "Wala makita ang user."})
    
    balance, gcash = row[0], row[1]
    
    if balance < 100.0:
        conn.close()
        return jsonify({"status": "error", "message": "Kinahanglan nga naa sa ₱100.00 pataas ang balanse aron makapag-withdraw!"})
    
    cursor.execute('UPDATE users SET balance = 0.0 WHERE gmail = ?', (gmail,))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": f"Malamposon nga na-withdraw ang ₱{balance} sa GCash number nga {gcash}!"})

if __name__ == '__main__':
    app.run(debug=True)