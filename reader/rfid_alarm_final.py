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
#API_URL = 'http://localhost:5000/receive'  # Change this if your API is hosted elsewhere  
API_URL = 'https://iqosgate.theorca.id/receive'  # Change this if your API is hosted elsewhere

# API endpoint to send gate status
GATE_STATUS_API_URL = 'https://iqosgate.theorca.id/gate_status'  # Change if needed
#GATE_STATUS_API_URL = 'http://localhost:5000/gate_status'  # Change if needed

# Device identifier for this Raspberry Pi
DEVICE_ID = "GateA"  # Change this to "GateB" or other as needed

def find_serial_port():
    """Find the first available serial port."""
    ports = list_ports.comports()
    if not ports:
        return None
        
    # Try to find a port with RFID reader characteristics
    for port in ports:
        # Print port details for debugging
        print(f"Found port: {port.device} - {port.description}")
        if "USB" in port.description.upper():
            print(f"Selected USB port: {port.device}")
            return port.device
            
    # If no specific USB port found, return the first available port
    print(f"Selected first available port: {ports[0].device}")
    return ports[0].device
  
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
  
    sent_tags = set()  
    last_clear_time = time.time()  
    CLEAR_INTERVAL = 60  # seconds to clear sent tags set  
    try:  
        # Open the serial port  
        with serial.Serial(serial_port, BAUD_RATE, timeout=1) as ser:  
            print(f"Listening for RFID tags on {serial_port}...")  
            while True:  
                current_time = time.time()  
                if current_time - last_clear_time > CLEAR_INTERVAL:  
                    sent_tags.clear()  
                    last_clear_time = current_time  
                    print("Cleared sent tags set.")  
                if ser.in_waiting > 0:  
                    rfid_tag = ser.read(ser.in_waiting)  # Read raw bytes  
                    print(f"Raw Data Detected: {rfid_tag}")  # Print raw data  
                    # Convert to hex string without spaces
                    tag_str = ''.join(format(x, '02x') for x in rfid_tag)
                    print(f"Raw Hex Data: {tag_str}")
                    
                    # Process the tag - remove first 4 bytes and last 2 bytes
                    hex_clean = tag_str[8:-4]  # Remove first 4 bytes (8 chars) and last 2 bytes (4 chars)
                    
                    # Take only first 24 characters (8 groups of 3 chars) and process into 12-bit chunks
                    hex_clean = hex_clean[:24]  # Limit to 24 characters
                    processed_chunks = []
                    for i in range(0, len(hex_clean), 3):
                        chunk = hex_clean[i:i+3]
                        if len(chunk) == 3:  # Only process complete 3-char chunks
                            processed_chunks.append(chunk)
                        if len(processed_chunks) == 8:  # Stop after 8 chunks
                            break
                            
                    # Join only the first 8 chunks with spaces
                    processed_tag = ' '.join(processed_chunks[:8])
                    print(f"Processed Hex Data (8 chunks of 12 bits): {processed_tag}")
                    
                    # Remove spaces for sending
                    processed_tag_no_spaces = ''.join(processed_chunks[:8])
                    
                    # Process the tag if it's not empty and hasn't been sent
                    if processed_tag_no_spaces and processed_tag_no_spaces not in sent_tags:
                        print(f"Sending new EPC tag: {processed_tag_no_spaces}")  
                        ring_alarm()  # Ring the alarm  
                        send_tag_to_api(processed_tag_no_spaces)  # Send tag to API  
                        sent_tags.add(processed_tag_no_spaces)  
                        time.sleep(1)  # Delay to avoid multiple alarms for the same tag  
                else:  
                    time.sleep(0.1)  
    except KeyboardInterrupt:  
        print("Program terminated.")  
    except Exception as e:  
        print(f"Error: {e}")  
  
if __name__ == "__main__":  
    main()
