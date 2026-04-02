const statusBadge = document.getElementById('status-badge');
const textInput = document.getElementById('text-input');
const speakBtn = document.getElementById('speak-btn');
const deviceInfo = document.getElementById('device-info');
const btnText = document.querySelector('.btn-text');
const loader = document.querySelector('.loader');

const API_URL = 'http://localhost:5000';

// Poll backend status
async function checkStatus() {
    try {
        const res = await fetch(`${API_URL}/status`);
        const data = await res.json();

        if (data.status === 'ready') {
            statusBadge.textContent = 'Model Ready';
            statusBadge.className = 'badge ready';
            textInput.disabled = false;
            speakBtn.disabled = false;
            deviceInfo.textContent = `Output routed to device ID: ${data.device_id}`;
            textInput.focus();
            return true; // Stop polling
        }
    } catch (err) {
        // Backend not up yet
    }
    return false; // Keep polling
}

// Start polling every second until ready
const pollInterval = setInterval(async () => {
    const isReady = await checkStatus();
    if (isReady) clearInterval(pollInterval);
}, 1000);

// Handle Speak Action
speakBtn.addEventListener('click', async () => {
    const text = textInput.value.trim();
    if (!text) return;

    // Set UI to loading state
    speakBtn.disabled = true;
    textInput.disabled = true;
    btnText.textContent = 'Speaking...';
    loader.classList.remove('hidden');

    try {
        await fetch(`${API_URL}/speak`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        // Clear text after successful speech
        textInput.value = '';
    } catch (err) {
        alert("Error sending request to backend.");
    } finally {
        // Restore UI state
        speakBtn.disabled = false;
        textInput.disabled = false;
        btnText.textContent = 'Speak';
        loader.classList.add('hidden');
        textInput.focus();
    }
});

// Trigger speak on Ctrl+Enter
textInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        speakBtn.click();
    }
});