import sqlite3
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
API_KEY = 'YOUR_OPENWEATHERMAP_API_KEY'
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'

def get_db():
    conn = sqlite3.connect('weather.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS weather_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            date TEXT NOT NULL,
            temp REAL NOT NULL,
            humidity INTEGER NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            predicted_date TEXT NOT NULL,
            predicted_temp REAL NOT NULL,
            actual_temp REAL,
            correction REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def fetch_weather(city):
    params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
    resp = requests.get(BASE_URL, params=params)
    if resp.status_code == 200:
        data = resp.json()
        return {
            'temp': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description']
        }
    return None

def predict_temp(city):
    conn = get_db()
    cursor = conn.execute('''
        SELECT temp FROM weather_history
        WHERE city = ? AND date = date('now', '-1 day')
        ORDER BY date DESC LIMIT 7
    ''', (city,))
    rows = cursor.fetchall()
    if len(rows) >= 3:
        temps = [r['temp'] for r in rows]
        predicted = sum(temps) / len(temps)
    else:
        predicted = 20.0
    conn.close()
    return round(predicted, 1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/weather')
def api_weather():
    city = request.args.get('city', 'Taipei')
    weather = fetch_weather(city)
    if not weather:
        return jsonify({'error': 'Failed to fetch weather'}), 400
    
    conn = get_db()
    today = datetime.now().strftime('%Y-%m-%d')
    conn.execute('''
        INSERT INTO weather_history (city, date, temp, humidity, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (city, today, weather['temp'], weather['humidity'], weather['description']))
    conn.commit()
    conn.close()
    
    prediction = predict_temp(city)
    return jsonify({**weather, 'prediction': prediction})

@app.route('/api/feedback', methods=['POST'])
def feedback():
    data = request.json
    city = data.get('city')
    predicted = data.get('predicted_temp')
    actual = data.get('actual_temp')
    
    if not all([city, predicted, actual]):
        return jsonify({'error': 'Missing data'}), 400
    
    correction = actual - predicted
    predicted_date = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db()
    conn.execute('''
        INSERT INTO predictions (city, predicted_date, predicted_temp, actual_temp, correction)
        VALUES (?, ?, ?, ?, ?)
    ''', (city, predicted_date, predicted, actual, correction))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'correction': correction})

@app.route('/api/history')
def history():
    city = request.args.get('city', 'Taipei')
    conn = get_db()
    cursor = conn.execute('''
        SELECT * FROM weather_history
        WHERE city = ?
        ORDER BY date DESC LIMIT 30
    ''', (city,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
