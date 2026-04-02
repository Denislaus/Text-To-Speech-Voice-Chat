import sounddevice as sd

print("Audio Devices:")
devices = sd.query_devices()
for i, dev in enumerate(devices):
    print(f"{i}: {dev['name']} - Input: {dev['max_input_channels']}, Output: {dev['max_output_channels']}")

print(f"\nDefault input device: {sd.default.device[0]}")
print(f"Default output device: {sd.default.device[1]}")