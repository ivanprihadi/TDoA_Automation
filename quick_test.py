from flask import Flask
import sys

print("[1] Creating Flask app...", flush=True)
app = Flask(__name__)

print("[2] Creating route...", flush=True)
@app.route('/')
def hello():
    return 'Hello from TDOA System!'

print("[3] Starting server...", flush=True)
if __name__ == '__main__':
    try:
        print("[4] Flask running on http://0.0.0.0:5000", flush=True)
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        sys.exit(1)
