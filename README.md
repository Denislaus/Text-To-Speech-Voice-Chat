ZeroPass Voice Synth 🎙️
A lightweight, local Text-to-Speech (TTS) application using the Piper engine and an Electron frontend. This app is designed to route synthesized speech directly into voice chats (Discord, Zoom, etc.) using a virtual audio bridge.

🛠️ Prerequisites
Python 3.8 - 3.11: Ensure Python is added to your PATH.

Node.js & NPM: Required to run the Electron frontend.

VB-CABLE (Windows): Essential for routing the app's audio into other software.

🔈 Setting up VB-CABLE (Virtual Audio Routing)
To make your voice chat "hear" the app, you need a virtual bridge.

Download: Go to VB-Audio's website and download the VB-CABLE Driver.

Install: Extract the ZIP and run VBCABLE_Setup_x64.exe as Administrator. Restart your computer after installation.

How it works: * The Python backend is programmed to automatically look for an output device named "CABLE Input".

It sends the speech to this "virtual input."

Voice Chat Setup: In your voice chat app (e.g., Discord), set your Input Device (Microphone) to CABLE Output (VB-Audio Virtual Cable).

🚀 Installation & Setup
1. Clone the Repository
Bash
git clone https://github.com/Denislaus/Text-To-Speech-Voice-Chat.git
cd Text-To-Speech-Voice-Chat
2. Setup Python Backend
We recommend using a virtual environment:

Bash
python -m venv venv
# Activate on Windows:
.\venv\Scripts\activate

# Install dependencies:
pip install -r requirements.txt
3. Download Voice Models
The app expects models in a models/ folder.

Create a folder named models in the root directory.

Download .onnx and .onnx.json files from the Piper Model Repository.

Ensure the filenames match the configuration in backend.py (e.g., bg_BG-dimitar-medium.onnx).

4. Setup Frontend
Bash
npm install
🏃 Running the Application
To start both the Flask backend and the Electron UI simultaneously:

Bash
npm start
Backend: Runs at http://localhost:5000

Frontend: Launches as a desktop window.

Shortcut: Use Ctrl + Enter in the text area to trigger speech quickly.

📂 Project Structure
backend.py: Flask server that handles speech synthesis and audio device routing.

main.js: Electron main process configuration.

renderer.js: Logic for the UI, model switching, and API communication.

index.html & styles.css: The "ZeroPass" themed dark UI.

⚠️ Troubleshooting
No Sound? Check your Windows Sound Settings. Ensure "CABLE Input" is visible under Playback devices. The app searches for this specific name to route audio.

Model Loading Error: Ensure both the .onnx and the .onnx.json files are present in the models/ folder.

Port Conflict: If port 5000 is in use, change it at the bottom of backend.py and the API_URL constant in renderer.js.