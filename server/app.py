from flask import Flask, request, jsonify, send_from_directory
import os
import json
from datetime import datetime, timezone, timedelta
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File to store the data
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rfid_data.json')
logger.info(f"Using data file: {DATA_FILE}")

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
    
    # Load current data
    current_data = load_data()
    logger.info("Loading current data for POST request")
    
    received_string = data['string']
    timestamp = data.get('timestamp', None)
    if timestamp:
        timestamp = format_timestamp_to_utc7(timestamp)
    
    # Add new data
    new_data = {'string': received_string, 'timestamp': timestamp}
    current_data.append(new_data)
    
    # Save to file
    save_data(current_data)
    logger.info(f"Saved new data, total records: {len(current_data)}")
    
    return jsonify({'message': 'String received', 'received': received_string, 'timestamp': timestamp}), 200

@app.route('/strings', methods=['GET'])
def get_strings():
    # Reload data from file for each request
    current_data = load_data()
    logger.info(f"Loaded {len(current_data)} records from file")
    return jsonify({'strings': current_data}), 200

@app.route('/')
def serve_index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

@app.route('/clear', methods=['GET', 'POST'])
def clear_strings():
    try:
        save_data([])
        logger.info("Cleared all RFID tag data")
        return jsonify({'message': 'All tags cleared'}), 200
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        return jsonify({'error': 'Failed to clear data'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
