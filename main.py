from flask import Flask, request, jsonify
import os
import psycopg
from urllib.parse import urlparse

app = Flask(__name__)

# Подключение к БД
def get_db_connection():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Для psycopg v3 подключение проще
        conn = psycopg.connect(DATABASE_URL)
        return conn
    return None

# Создание таблицы при старте
def init_db():
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
        conn.close()

# Инициализируем БД при запуске
init_db()

@app.route('/')
def hello():
    return "Hello, Serverless! 🚀\n", 200, {'Content-Type': 'text/plain'}

@app.route('/echo', methods=['POST'])
def echo():
    data = request.get_json()
    return jsonify({
        "status": "received",
        "you_sent": data,
        "length": len(str(data)) if data else 0
    })

@app.route('/save', methods=['POST'])
def save_message():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    data = request.get_json()
    message = data.get('message', '') if data else ''

    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
            conn.commit()
        conn.close()
        return jsonify({"status": "saved", "message": message})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/messages')
def get_messages():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
        conn.close()

        messages = [{"id": r[0], "text": r[1], "time": r[2].isoformat()} for r in rows]
        return jsonify(messages)
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)