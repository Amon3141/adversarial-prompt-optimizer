from flask import Flask, render_template, request, jsonify
from gan_loop import GANLoop
import threading
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
gan = GANLoop()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_loop():
    rounds = int(request.json.get('rounds', 1))
    if not gan.is_running:
        thread = threading.Thread(target=gan.run_loop, args=(rounds,))
        thread.start()
        return jsonify({"status": "started", "message": f"Started loop for {rounds} rounds"})
    return jsonify({"status": "error", "message": "Already running"})

@app.route('/status')
def status():
    return jsonify(gan.get_status())

@app.route('/stop', methods=['POST'])
def stop_loop():
    gan.stop()
    return jsonify({"status": "stopped"})

if __name__ == '__main__':
    app.run(debug=True, port=8080)
