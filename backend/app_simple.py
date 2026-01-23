from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

sleep_records = []

def parse_datetime(dt_str):
    if not dt_str:
        return None
    try:
        if 'Z' in dt_str:
            dt_str = dt_str.replace('Z', '+00:00')
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return None

def get_weekday_name(dt):
    if not dt:
        return "Неизвестно"
    days = [
        "Понедельник", "Вторник", "Среда", "Четверг",
        "Пятница", "Суббота", "Воскресенье"
    ]
    return days[dt.weekday()]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'records': len(sleep_records)
    })

@app.route('/api/sleep', methods=['POST'])
def save_sleep():
    data = request.get_json()

    if not data or 'start_time' not in data or 'end_time' not in data:
        return jsonify({
            'status': 'error',
            'message': 'start_time и end_time обязательны'
        }), 400

    start_dt = parse_datetime(data['start_time'])
    end_dt = parse_datetime(data['end_time'])

    if not start_dt or not end_dt or start_dt >= end_dt:
        return jsonify({
            'status': 'error',
            'message': 'Некорректное время сна'
        }), 400

    duration_hours = round((end_dt - start_dt).total_seconds() / 3600, 2)

    habits = data.get('digital_habits', {})
    screen_time = habits.get('screen_time_minutes', 0)
    social_time = habits.get('social_media_minutes', 0)
    gaming_time = habits.get('gaming_minutes', 0)

    quality_score = max(0, min(100, 100 - screen_time * 0.25))

    recommendations = []
    if screen_time > 120:
        recommendations.append('Сократите экранное время перед сном')
    if duration_hours < 6.5:
        recommendations.append('Сон короче нормы, увеличьте продолжительность')
    if not recommendations:
        recommendations.append('Привычки нормальные')

    record = {
        'id': len(sleep_records) + 1,
        'user_id': data.get('user_id', 1),
        'start_time': data['start_time'],
        'end_time': data['end_time'],
        'day_of_week': get_weekday_name(start_dt),
        'sleep_hours': duration_hours,
        'analysis': {
            'duration_hours': duration_hours,
            'quality_score': round(quality_score, 1),
            'screen_time': screen_time,
            'social_media_time': social_time,
            'gaming_time': gaming_time
        },
        'recommendations': recommendations,
        'timestamp': datetime.now().isoformat()
    }

    sleep_records.append(record)

    return jsonify({
        'status': 'success',
        'record_id': record['id'],
        'day_of_week': record['day_of_week'],
        'sleep_hours': duration_hours,
        'analysis': record['analysis'],
        'recommendations': recommendations
    })

@app.route('/api/sleep/user/<int:user_id>')
def get_user_history(user_id):
    user_records = [r for r in sleep_records if r.get('user_id') == user_id]
    return jsonify({
        'status': 'success',
        'records_count': len(user_records),
        'records': user_records[-10:]
    })

@app.route('/api/sleep/stats/weekly')
def weekly_stats():
    if not sleep_records:
        return jsonify({'status': 'success', 'weekly_stats': []})

    days_order = [
        "Понедельник", "Вторник", "Среда", "Четверг",
        "Пятница", "Суббота", "Воскресенье"
    ]

    stats = []
    for day_name in days_order:
        day_records = [r for r in sleep_records if r['day_of_week'] == day_name]
        if day_records:
            avg_hours = sum(r['sleep_hours'] for r in day_records) / len(day_records)
            stats.append({
                'day': day_name,
                'avg_hours': round(avg_hours, 2),
                'record_count': len(day_records)
            })
        else:
            stats.append({
                'day': day_name,
                'avg_hours': 0,
                'record_count': 0
            })

    return jsonify({
        'status': 'success',
        'weekly_stats': stats
    })

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
