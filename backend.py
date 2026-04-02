from flask import Flask, request, jsonify
from flask_cors import CORS
import sounddevice as sd
import numpy as np
from piper import PiperVoice
import os
import threading

app = Flask(__name__)
CORS(app)

# Configuration for available models
# Add your downloaded models here. Ensure the .onnx and .onnx.json files exist.
AVAILABLE_MODELS = {
    "bg_BG-dimitar-medium": {
        "id": "bg_BG-dimitar-medium",
        "name": "Dimitar (Medium)",
        "language": "Bulgarian",
        "path": "models/bg_BG-dimitar-medium.onnx",       # <-- Added models/
        "config": "models/bg_BG-dimitar-medium.onnx.json" # <-- Added models/
    },
    "en_US-lessac-medium": {
        "id": "en_US-lessac-medium",
        "name": "Lessac (Medium)",
        "language": "English",
        "path": "models/voice-model.onnx",                # <-- Updated to match the file in your directory
        "config": "models/voice-model.onnx.json"          # <-- Updated to match the file in your directory
    }
}

# Globals state
active_model_id = "bg_BG-dimitar-medium"
voice = None
sample_rate = None
device_id = None
is_ready = False
is_loading = False

def get_vbcable_device_id():
    try:
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if "CABLE Input" in dev['name'] and dev['max_output_channels'] > 0:
                return i
    except Exception as e:
        print(f"Error querying devices: {e}")
    return sd.default.device[1]

def load_model(model_id):
    global voice, sample_rate, device_id, is_ready, is_loading, active_model_id
    
    is_loading = True
    is_ready = False
    active_model_id = model_id
    
    print(f"Initializing Model: {model_id}...")
    device_id = get_vbcable_device_id()
    
    model_info = AVAILABLE_MODELS.get(model_id)
    if not model_info:
        print(f"Model {model_id} not found in configuration.")
        is_loading = False
        return False

    model_path = model_info["path"]
    config_path = model_info["config"]

    if os.path.exists(model_path) and os.path.exists(config_path):
        try:
            voice = PiperVoice.load(model_path, config_path=config_path)
            sample_rate = voice.config.sample_rate
            is_ready = True
            print(f"Ready. Routed to device: {device_id}")
        except Exception as e:
            print(f"Failed to load model: {e}")
    else:
        print(f"Model files missing for {model_id}! Please check the paths.")
    
    is_loading = False
    return is_ready

@app.route('/models', methods=['GET'])
def get_models():
    # Group models by language for the frontend
    languages = {}
    for key, data in AVAILABLE_MODELS.items():
        lang = data["language"]
        if lang not in languages:
            languages[lang] = []
        languages[lang].append({"id": data["id"], "name": data["name"]})
    
    return jsonify({
        "active": active_model_id,
        "languages": languages
    })

@app.route('/set_model', methods=['POST'])
def set_model():
    data = request.json
    model_id = data.get("model_id")
    
    if not model_id or model_id not in AVAILABLE_MODELS:
        return jsonify({"error": "Invalid model ID"}), 400
        
    # Load in background so we don't block the request entirely
    threading.Thread(target=load_model, args=(model_id,)).start()
    return jsonify({"success": True, "message": "Model loading started"})

@app.route('/status', methods=['GET'])
def status():
    if is_ready:
        return jsonify({"status": "ready", "device_id": device_id, "active_model": active_model_id})
    elif is_loading:
        return jsonify({"status": "loading"})
    else:
        return jsonify({"status": "error", "message": "Model failed to load or missing files"})

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
    # Load default model in a background thread
    threading.Thread(target=load_model, args=(active_model_id,)).start()
    app.run(port=5000, debug=False, use_reloader=False)