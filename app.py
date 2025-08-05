from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

LOG_FILE = "visitors.log"

def get_ip():
    # Try to get real IP behind proxies (like Render)
    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"].split(',')[0].strip()
    return request.remote_addr

@app.route('/')
def home():
    ip = get_ip()
    user_agent = request.headers.get('User-Agent')
    path = request.path
    method = request.method
    url = request.url
    referrer = request.referrer
    headers = dict(request.headers)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = (
        f"[{timestamp}]\n"
        f"IP: {ip}\n"
        f"Method: {method}\n"
        f"Path: {path}\n"
        f"URL: {url}\n"
        f"Referrer: {referrer}\n"
        f"User-Agent: {user_agent}\n"
        f"Headers: {headers}\n"
        f"{'-'*60}\n"
    )

    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except Exception as e:
        return f"Error logging: {e}"

    return f"Your IP ({ip}) has been recorded!"

@app.route('/show-log')
def show_log():
    try:
        with open(LOG_FILE, "r") as f:
            return f"<pre>{f.read()}</pre>"
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True)
