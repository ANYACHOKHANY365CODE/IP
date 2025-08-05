from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    print(f"User IP: {user_ip}")
    return render_template_string("""
        <h1>Welcome!</h1>
    """)
