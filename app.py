from flask import Flask, request
from datetime import datetime
import ipaddress
import requests
import os
import logging
from supabase import create_client, Client

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = None

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    logger.info("Supabase connected successfully")
else:
    logger.warning("Supabase credentials not found, using local storage")

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

    # Prepare visitor data
    visitor_data = {
        "timestamp": timestamp,
        "ip_address": ip,
        "location_info": location_info,
        "user_agent": user_agent,
        "method": method,
        "path": path,
        "url": url,
        "referrer": referrer,
        "remote_addr": request.remote_addr,
        "headers": str(headers)
    }

    # Save to Supabase if available, otherwise use local file
    try:
        if supabase:
            # Save to Supabase database
            result = supabase.table('visitors').insert(visitor_data).execute()
            logger.info(f"Saved to Supabase: {ip}")
        else:
            # Fallback to local file
            LOG_FILE = "visitors.log"
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
            
            with open(LOG_FILE, "a") as f:
                f.write(log_entry)
            logger.info(f"Saved to local file: {ip}")
    except Exception as e:
        logger.error(f"Error saving visitor data: {e}")
        return f"Error logging: {e}"

    return f"Your IP ({ip}) has been recorded!"

@app.route('/show-log')
def show_log():
    try:
        if supabase:
            # Get data from Supabase
            result = supabase.table('visitors').select('*').order('timestamp', desc=True).execute()
            visitors = result.data
            
            # Format the data
            content = ""
            for visitor in visitors:
                content += f"[{visitor['timestamp']}]\n"
                content += f"IP: {visitor['ip_address']}\n"
                content += f"Location: {visitor['location_info']}\n"
                content += f"Method: {visitor['method']}\n"
                content += f"Path: {visitor['path']}\n"
                content += f"URL: {visitor['url']}\n"
                content += f"Referrer: {visitor['referrer']}\n"
                content += f"User-Agent: {visitor['user_agent']}\n"
                content += f"Headers: {visitor['headers']}\n"
                content += "-" * 60 + "\n"
        else:
            # Fallback to local file
            with open("visitors.log", "r") as f:
                content = f.read()
        
        return f"<pre>{content}</pre>"
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

@app.route('/visitors')
def show_visitors():
    """Show recent visitors in a web interface"""
    try:
        if supabase:
            # Get data from Supabase
            result = supabase.table('visitors').select('*').order('timestamp', desc=True).execute()
            visitors = result.data
            
            # Format the data
            content = ""
            for visitor in visitors:
                content += f"[{visitor['timestamp']}]\n"
                content += f"IP: {visitor['ip_address']}\n"
                content += f"Location: {visitor['location_info']}\n"
                content += f"Method: {visitor['method']}\n"
                content += f"Path: {visitor['path']}\n"
                content += f"URL: {visitor['url']}\n"
                content += f"Referrer: {visitor['referrer']}\n"
                content += f"User-Agent: {visitor['user_agent']}\n"
                content += f"Headers: {visitor['headers']}\n"
                content += "-" * 60 + "\n"
        else:
            # Fallback to local file
            with open("visitors.log", "r") as f:
                content = f.read()
        
        return f"""
        <html>
        <head>
            <title>Recent Visitors</title>
            <meta http-equiv="refresh" content="10">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .header {{ background: #007bff; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📊 Recent Visitors</h2>
                <p>Auto-refreshes every 10 seconds</p>
            </div>
            <pre>{content}</pre>
        </body>
        </html>
        """
    except Exception as e:
        return f"Error reading log: {e}"

@app.route('/api/visitors')
def api_visitors():
    """API endpoint to get visitor data as JSON"""
    try:
        if supabase:
            # Get data from Supabase
            result = supabase.table('visitors').select('*').order('timestamp', desc=True).execute()
            visitors = result.data
            
            # Format the data
            content = ""
            for visitor in visitors:
                content += f"[{visitor['timestamp']}]\n"
                content += f"IP: {visitor['ip_address']}\n"
                content += f"Location: {visitor['location_info']}\n"
                content += f"Method: {visitor['method']}\n"
                content += f"Path: {visitor['path']}\n"
                content += f"URL: {visitor['url']}\n"
                content += f"Referrer: {visitor['referrer']}\n"
                content += f"User-Agent: {visitor['user_agent']}\n"
                content += f"Headers: {visitor['headers']}\n"
                content += "-" * 60 + "\n"
        else:
            # Fallback to local file
            with open("visitors.log", "r") as f:
                content = f.read()
        
        return {"visitors_log": content, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
