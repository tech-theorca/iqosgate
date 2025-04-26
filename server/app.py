from flask import Flask, request, jsonify, send_from_directory
import os
import json
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# File to store the data
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rfid_data.json')

# Load existing data or initialize empty list
def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading data: {e}")
        return []

# Save data to file
def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving data: {e}")

# Initialize data from file
received_strings = load_data()

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
    
    # Add new data
    new_data = {'string': received_string, 'timestamp': timestamp}
    received_strings.append(new_data)
    
    # Save to file
    save_data(received_strings)
    
    return jsonify({'message': 'String received', 'received': received_string, 'timestamp': timestamp}), 200

@app.route('/strings', methods=['GET'])
def get_strings():
    return jsonify({'strings': received_strings}), 200

@app.route('/')
def serve_index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
