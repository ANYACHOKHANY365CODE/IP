from flask import Flask, request
from datetime import datetime
from werkzeug.middleware.proxy_fix import ProxyFix
import requests
import os
import ipaddress

app = Flask(__name__)
LOG_FILE = "visitors.log"


def get_ip():
    # Get X-Forwarded-For and split
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    ip_list = [ip.strip() for ip in forwarded_for.split(",") if ip.strip()]

    # Return the first public (non-private) IP
    for ip in ip_list:
        try:
            if not ipaddress.ip_address(ip).is_private:
                return ip
        except ValueError:
            continue

    # Fallback to remote_addr
    try:
        if not ipaddress.ip_address(request.remote_addr).is_private:
            return request.remote_addr
    except ValueError:
        pass

    return "Unknown"

def get_location_info(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=3)
        if response.status_code == 200:
            data = response.json()
            city = data.get("city", "Unknown")
            region = data.get("region", "Unknown")
            country = data.get("country", "Unknown")
            org = data.get("org", "Unknown")
            loc = data.get("loc", "Unknown")
            return f"{city}, {region}, {country} | Org: {org} | Coords: {loc}"
    except:
        pass
    return "Location info unavailable"

@app.route('/')
def home():
    ip = get_ip()
    location_info = get_location_info(ip)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    path = request.path
    method = request.method
    url = request.url
    referrer = request.referrer or "None"
    headers = dict(request.headers)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = (
        f"[{timestamp}]\n"
        f"IP: {ip}\n"
        f"Location: {location_info}\n"
        f"Method: {method}\n"
        f"Path: {path}\n"
        f"URL: {url}\n"
        f"Referrer: {referrer}\n"
        f"User-Agent: {user_agent}\n"
        f"Headers:\n"
    )

    for key, value in headers.items():
        log_entry += f"  {key}: {value}\n"

    log_entry += "-" * 60 + "\n"

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

