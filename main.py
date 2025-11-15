from flask import Flask, request, jsonify
import os
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)


# Подключение к БД
def get_db_connection():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Исправляем формат URL для совместимости
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

        url = urlparse(DATABASE_URL)
        try:
            conn = psycopg2.connect(
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port
            )
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    return None


# Создание таблицы при старте
def init_db():
    conn = get_db_connection()
    if conn:
        try:
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
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"Database init error: {e}")


# Инициализируем БД при запуске
init_db()


# Задание 1: Главная страница
@app.route('/')
def hello():
    return "Hello, Serverless! 🚀\n", 200, {'Content-Type': 'text/plain'}


# Задание 2: Эндпоинт для обработки JSON
@app.route('/echo', methods=['POST'])
def echo():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    return jsonify({
        "status": "received",
        "you_sent": data,
        "length": len(str(data))
    })


# Задание 3: Работа с базой данных
@app.route('/save', methods=['POST'])
def save_message():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database not connected"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    message = data.get('message', '')
    if not message:
        return jsonify({"error": "Message field is required"}), 400

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
        return jsonify({"error": "Database not connected"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, content, created_at FROM messages ORDER BY created_at DESC LIMIT 10")
            rows = cur.fetchall()
        conn.close()

        messages = []
        for row in rows:
            messages.append({
                "id": row[0],
                "text": row[1],
                "time": row[2].isoformat() if row[2] else None
            })

        return jsonify(messages)
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


# Дополнительный эндпоинт для проверки статуса
@app.route('/health')
def health():
    conn = get_db_connection()
    db_status = "connected" if conn else "disconnected"
    if conn:
        conn.close()

    return jsonify({
        "status": "ok",
        "database": db_status,
        "endpoints": {
            "GET /": "Hello message",
            "POST /echo": "Echo JSON data",
            "POST /save": "Save message to database",
            "GET /messages": "Get all messages",
            "GET /health": "Health check"
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)