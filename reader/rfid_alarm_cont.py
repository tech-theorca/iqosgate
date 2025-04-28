import serial  
import time  
import pygame  # Import pygame for sound playback  
import requests  # Import requests to send HTTP requests  
from datetime import datetime  
from serial.tools import list_ports  
  
# Configure the baud rate  
BAUD_RATE = 57600  # Change this to your RFID reader's baud rate  
  
# Path to your custom alarm sound  
ALARM_SOUND = 'alarm_sound.mp3'  # Change this to your audio file path  
  
# API endpoint to send RFID tags  
# API_URL = 'http://localhost:5000/receive'  # Change this if your API is hosted elsewhere  
API_URL = 'https://iqosgate.theorca.id/receive'  # Change this if your API is hosted elsewhere

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
        response = requests.post(API_URL, json={'string': tag_str, 'timestamp': timestamp})  
        if response.status_code == 200:  
            print(f"Successfully sent tag to API: {tag_str} at {timestamp}")  
        else:  
            print(f"Failed to send tag to API: {response.status_code} {response.text}")  
    except Exception as e:  
        print(f"Error sending tag to API: {e}")  
  
def main():  
    serial_port = find_serial_port()  
    if not serial_port:  
        print("No serial port found. Please connect your RFID reader.")  
        return  
  
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
