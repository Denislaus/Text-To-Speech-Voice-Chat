import sounddevice as sd
import numpy as np
from piper import PiperVoice
import sys
import os

# --- Configuration ---
MODEL_PATH = "bg_BG-dimitar-medium.onnx"
CONFIG_PATH = "bg_BG-dimitar-medium.onnx.json"

def get_vbcable_device_id():
    """Finds the VB-Cable playback device ID."""
    try:
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if "CABLE Input" in dev['name'] and dev['max_output_channels'] > 0:
                return i
    except Exception as e:
        print(f"Error querying audio devices: {e}")
    return None

def main():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(CONFIG_PATH):
        print("Error: Piper model or config file not found.")
        sys.exit(1)

    print("Searching for VB-Cable...")
    device_id = get_vbcable_device_id()
    
    if device_id is not None:
        print(f"[SUCCESS] Routed to VB-Cable (Device ID: {device_id}).")
    else:
        print("[WARNING] VB-Cable not found! Defaulting to standard speakers.")
        device_id = sd.default.device[1]

    print("\nLoading Piper TTS model...")
    voice = PiperVoice.load(MODEL_PATH, config_path=CONFIG_PATH)
    sample_rate = voice.config.sample_rate

    print("\n--- Local TTS Router Active ---")
    print("Type text and press Enter. Ctrl+C to exit.\n")

    while True:
        try:
            text = input("Say: ")
            if not text.strip():
                continue

            # We collect all chunks into a list of numpy arrays
            audio_chunks = []
            
            # In Piper 1.4.1+, synthesize() yields AudioChunk objects.
            for chunk in voice.synthesize(text):
                
                # 1. Extract the raw bytes from the AudioChunk object
                # [FIXED] Changed chunk.audio to chunk.audio_int16_bytes
                raw_bytes = chunk.audio_int16_bytes
                
                # 2. Convert those bytes into a 16-bit NumPy array
                audio_data = np.frombuffer(raw_bytes, dtype=np.int16)
                
                # 3. Add to our list
                audio_chunks.append(audio_data.flatten())

            if audio_chunks:
                # Combine all chunks into one single array
                full_audio = np.concatenate(audio_chunks)

                # Ensure audio is mono (single channel) for compatibility
                if full_audio.ndim > 1:
                    full_audio = full_audio[:, 0] if full_audio.shape[1] > 1 else full_audio.flatten()

                # Get device info to check output channels
                device_info = sd.query_devices(device=device_id)
                max_channels = device_info['max_output_channels']

                if max_channels >= 2:
                    # Device supports stereo or more, duplicate mono to stereo for better compatibility
                    full_audio = np.column_stack((full_audio, full_audio))

                # Play to VB-Cable
                sd.play(full_audio, samplerate=sample_rate, device=device_id)
                sd.wait() 

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    main()