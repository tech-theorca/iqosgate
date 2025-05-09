import serial  
import time  
import pygame  # Import pygame for sound playback  
import requests  # Import requests to send HTTP requests  
from datetime import datetime  
from serial.tools import list_ports  
import threading  
  
# Configure the baud rate  
BAUD_RATE = 57600  # Change this to your RFID reader's baud rate  
  
# Path to your custom alarm sound  
ALARM_SOUND = 'alarm_sound.mp3'  # Change this to your audio file path  
  
# API endpoint to send RFID tags  
# API_URL = 'http://localhost:5000/receive'  # Change this if your API is hosted elsewhere  
API_URL = 'https://iqosgate.theorca.id/receive'  # Change this if your API is hosted elsewhere

# API endpoint to send gate status
GATE_STATUS_API_URL = 'https://iqosgate.theorca.id/gate_status'  # Change if needed

# Device identifier for this Raspberry Pi
DEVICE_ID = "GateA"  # Change this to "GateB" or other as needed

def find_serial_port():  
    ports = list_ports.comports()  
    for port in ports:  
        # You can add more sophisticated checks here if needed  
        print(f"Found port: {port.device} - {port.description}")  
        return port.device  
    return None  
 
def ring_alarm():  
    pygame.mixer.init()  # Initialize the mixer  
    pygame.mixer.music.load(ALARM_SOUND)  # Load the sound file  
    pygame.mixer.music.play()  # Play the sound  
 
def send_tag_to_api(tag_str):  
    try:  
        timestamp = datetime.utcnow().isoformat() + 'Z'  # UTC ISO 8601 format  
        response = requests.post(API_URL, json={'string': tag_str, 'timestamp': timestamp, 'device': DEVICE_ID})  
        if response.status_code == 200:  
            print(f"Successfully sent tag to API: {tag_str} at {timestamp} from {DEVICE_ID}")  
        else:  
            print(f"Failed to send tag to API: {response.status_code} {response.text}")  
    except Exception as e:  
        print(f"Error sending tag to API: {e}")  

def send_gate_status_to_api(status):  
    try:  
        response = requests.post(GATE_STATUS_API_URL, json={'gate_id': DEVICE_ID, 'status': status})  
        if response.status_code == 200:  
            print(f"Successfully sent gate status {status} for {DEVICE_ID}")  
        else:  
            print(f"Failed to send gate status: {response.status_code} {response.text}")  
    except Exception as e:  
        print(f"Error sending gate status: {e}")  

def periodic_gate_status_update(interval=60):  
    status = 1  # Hardcoded online status, can be updated with real logic  
    # Send initial online status immediately on start
    send_gate_status_to_api(status)
    while True:  
        time.sleep(interval)  
        send_gate_status_to_api(status)  

def main():  
    serial_port = find_serial_port()  
    if not serial_port:  
        print("No serial port found. Please connect your RFID reader.")  
        return  
 
    # Start the periodic gate status update in a separate thread  
    threading.Thread(target=periodic_gate_status_update, daemon=True).start()  
 
    try:  
        # Open the serial port  
        with serial.Serial(serial_port, BAUD_RATE, timeout=1) as ser:  
            print(f"Listening for RFID tags on {serial_port}...")  
            while True:  
                if ser.in_waiting > 0:  
                    rfid_tag = ser.read(ser.in_waiting)  # Read raw bytes  
                    print(f"Raw Data Detected: {rfid_tag}")  # Print raw data  
                    # Convert to hex string for sending  
                    tag_str = ''.join(format(x, '02x') for x in rfid_tag)  
                    print(f"Hex Data: {tag_str}")  
                    # Split hex string into chunks of 16 characters (8 bytes)  
                    chunk_size = 16  
                    for i in range(0, len(tag_str), chunk_size):  
                        chunk = tag_str[i:i+chunk_size]  
                        if chunk:  
                            print(f"Sending EPC chunk: {chunk}")  
                            ring_alarm()  # Ring the alarm  
                            send_tag_to_api(chunk)  # Send chunk to API  
                            time.sleep(1)  # Delay to avoid multiple alarms for the same tag  
                else:  
                    time.sleep(0.1)  
    except KeyboardInterrupt:  
        print("Program terminated.")  
    except Exception as e:  
        print(f"Error: {e}")  
 
if __name__ == "__main__":  
    main()
