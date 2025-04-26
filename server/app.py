from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# In-memory storage for received strings with timestamps
received_strings = []

def format_timestamp_to_utc7(iso_timestamp):
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        utc7 = timezone(timedelta(hours=7))
        dt_utc7 = dt.astimezone(utc7)
        day = dt_utc7.strftime('%A')  # Full weekday name
        time = dt_utc7.strftime('%H:%M:%S')
        return f"{day} {time}"
    except Exception:
        return iso_timestamp

@app.route('/receive', methods=['POST'])
def receive_string():
    data = request.get_json()
    if not data or 'string' not in data:
        return jsonify({'error': 'Missing "string" in request body'}), 400
    received_string = data['string']
    timestamp = data.get('timestamp', None)
    if timestamp:
        timestamp = format_timestamp_to_utc7(timestamp)
    received_strings.append({'string': received_string, 'timestamp': timestamp})
    return jsonify({'message': 'String received', 'received': received_string, 'timestamp': timestamp}), 200

@app.route('/strings', methods=['GET'])
def get_strings():
    return jsonify({'strings': received_strings}), 200

@app.route('/')
def serve_index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
