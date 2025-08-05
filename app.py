from flask import Flask, request
from datetime import datetime
import json
from user_agents import parse

app = Flask(__name__)

@app.route('/')
def home():
    # Get IP Address
    forwarded_for = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip = forwarded_for.split(',')[0].strip()

    # Get time
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Get User-Agent
    user_agent_string = request.headers.get('User-Agent')
    user_agent = parse(user_agent_string)

    # Log detailed device info
    device_info = {
        'datetime': now,
        'ip': ip,
        'user_agent_raw': user_agent_string,
        'browser': user_agent.browser.family + " " + user_agent.browser.version_string,
        'os': user_agent.os.family + " " + user_agent.os.version_string,
        'device': user_agent.device.family,
        'is_mobile': user_agent.is_mobile,
        'is_tablet': user_agent.is_tablet,
        'is_pc': user_agent.is_pc,
        'is_bot': user_agent.is_bot
    }

    # Save to file
    with open("ip_log.txt", "a", encoding="utf-8") as f:
        f.write(json.dumps(device_info, ensure_ascii=False) + "\n")

    return f"Your IP ({ip}) has been recorded!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
