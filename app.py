from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def get_ip():
    # Get the IP address of the visitor
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Get timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Save to a file
    with open('ips.txt', 'a') as file:
        file.write(f"{timestamp} - {ip_address}\n")

    return f"Your IP address is {ip_address}"
