"""Simple TDOA Dashboard"""
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from pathlib import Path

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify({
        'system': 'running',
        'version': '1.0.0',
        'receivers': 3
    })

if __name__ == '__main__':
    Path('logs').mkdir(exist_ok=True)
    Path('output').mkdir(exist_ok=True)
    print("\n🛰️  TDOA System Starting...")
    print("=" * 60)
    print("Running on http://0.0.0.0:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)
