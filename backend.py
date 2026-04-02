from flask import Flask, request, jsonify
from flask_cors import CORS
import sounddevice as sd
import numpy as np
from piper import PiperVoice
import os
import sys
import threading

app = Flask(__name__)
CORS(app)

# Configuration
MODEL_PATH = "bg_BG-dimitar-medium.onnx"
CONFIG_PATH = "bg_BG-dimitar-medium.onnx.json"

# Globals state
voice = None
sample_rate = None
device_id = None
is_ready = False

def get_vbcable_device_id():
    try:
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if "CABLE Input" in dev['name'] and dev['max_output_channels'] > 0:
                return i
    except Exception as e:
        print(f"Error querying devices: {e}")
    return sd.default.device[1]

def initialize_tts():
    global voice, sample_rate, device_id, is_ready
    print("Initializing Model & Devices...")
    device_id = get_vbcable_device_id()
    if os.path.exists(MODEL_PATH) and os.path.exists(CONFIG_PATH):
        voice = PiperVoice.load(MODEL_PATH, config_path=CONFIG_PATH)
        sample_rate = voice.config.sample_rate
        is_ready = True
        print(f"Ready. Routed to device: {device_id}")
    else:
        print("Model files missing!")

@app.route('/status', methods=['GET'])
def status():
    if is_ready:
        return jsonify({"status": "ready", "device_id": device_id})
    return jsonify({"status": "loading"})

@app.route('/speak', methods=['POST'])
def speak():
    if not is_ready:
        return jsonify({"error": "Model not loaded yet"}), 503

    data = request.json
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        audio_chunks = []
        for chunk in voice.synthesize(text):
            raw_bytes = chunk.audio_int16_bytes
            audio_data = np.frombuffer(raw_bytes, dtype=np.int16)
            audio_chunks.append(audio_data.flatten())

        if audio_chunks:
            full_audio = np.concatenate(audio_chunks)
            if full_audio.ndim > 1:
                full_audio = full_audio[:, 0] if full_audio.shape[1] > 1 else full_audio.flatten()

            device_info = sd.query_devices(device=device_id)
            if device_info['max_output_channels'] >= 2:
                full_audio = np.column_stack((full_audio, full_audio))

            sd.play(full_audio, samplerate=sample_rate, device=device_id)
            sd.wait() 
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Load model in a background thread so the server starts immediately
    threading.Thread(target=initialize_tts).start()
    # Run on local port 5000
    app.run(port=5000, debug=False, use_reloader=False)