from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{now} - {ip}\n"

    try:
        with open("ip_log.txt", "a") as f:
            f.write(log_entry)
    except Exception as e:
        return f"Error writing IP: {e}"

    return f"Your IP ({ip}) has been recorded!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
