from flask import Flask, request
from datetime import datetime
import ipaddress
import requests
import os
import logging

app = Flask(__name__)
LOG_FILE = "visitors.log"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_ip():
    # Check all possible proxy headers for the real IP
    proxy_headers = [
        'X-Real-IP',
        'X-Forwarded-For', 
        'X-Client-IP',
        'CF-Connecting-IP',  # Cloudflare
        'X-Forwarded',
        'Forwarded-For',
        'Forwarded'
    ]
    
    # First, try to get IP from proxy headers
    for header in proxy_headers:
        if header in request.headers:
            ip_value = request.headers[header]
            if ip_value:
                # Handle comma-separated lists (common in X-Forwarded-For)
                ip_list = [ip.strip() for ip in ip_value.split(",") if ip.strip()]
                
                for ip in ip_list:
                    try:
                        ip_obj = ipaddress.ip_address(ip)
                        # Return the first public IP we find
                        if not ip_obj.is_private and not ip_obj.is_loopback:
                            return ip
                    except ValueError:
                        continue
    
    # Fallback to remote_addr only if it's public
    try:
        ip_obj = ipaddress.ip_address(request.remote_addr)
        if not ip_obj.is_private and not ip_obj.is_loopback:
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

    # Log the detected IP to terminal for visibility
    logger.info(f"[{timestamp}] Visitor IP: {ip} | Remote: {request.remote_addr}")
    logger.info(f"Request from: {request.remote_addr} -> Detected IP: {ip}")

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
        logger.error(f"Error logging: {e}")
        return f"Error logging: {e}"

    return f"Your IP ({ip}) has been recorded!"

@app.route('/show-log')
def show_log():
    try:
        with open(LOG_FILE, "r") as f:
            return f"<pre>{f.read()}</pre>"
    except Exception as e:
        return str(e)

@app.route('/debug-headers')
def debug_headers():
    """Debug route to show all request headers for troubleshooting"""
    headers_info = "Request Headers:\n"
    for key, value in request.headers.items():
        headers_info += f"{key}: {value}\n"
    
    headers_info += f"\nRemote Address: {request.remote_addr}\n"
    headers_info += f"Detected IP: {get_ip()}\n"
    
    return f"<pre>{headers_info}</pre>"

@app.route('/health')
def health():
    """Health check route for deployment platforms"""
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
