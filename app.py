from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to Schwab Bot!"

@app.route('/healthz')
def health_check():
    return jsonify(status="healthy"), 200

@app.route('/status')
def status():
    return jsonify(status="running"), 200

# Schwab authentication placeholder
# Place your Schwab auth logic here

if __name__ == '__main__':
    app.run(debug=True)