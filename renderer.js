const statusBadge = document.getElementById('status-badge');
const textInput = document.getElementById('text-input');
const speakBtn = document.getElementById('speak-btn');
const deviceInfo = document.getElementById('device-info');
const btnText = document.querySelector('.btn-text');
const loader = document.querySelector('.loader');

const langSelect = document.getElementById('language-select');
const voiceSelect = document.getElementById('voice-select');

const API_URL = 'http://localhost:5000';
let availableModels = {};
let currentActiveModel = "";
let pollInterval = null; // Variable to keep track of the polling loop

// Fetch available models from backend
async function fetchModels() {
    try {
        const res = await fetch(`${API_URL}/models`);
        const data = await res.json();
        availableModels = data.languages;
        currentActiveModel = data.active;

        populateLanguageDropdown();
    } catch (err) {
        console.error("Failed to fetch models", err);
    }
}

function populateLanguageDropdown() {
    langSelect.innerHTML = '';
    const languages = Object.keys(availableModels);

    languages.forEach(lang => {
        const option = document.createElement('option');
        option.value = lang;
        option.textContent = lang;
        langSelect.appendChild(option);
    });

    // Find language of the active model
    let activeLang = languages[0];
    for (const [lang, models] of Object.entries(availableModels)) {
        if (models.some(m => m.id === currentActiveModel)) {
            activeLang = lang;
            break;
        }
    }

    langSelect.value = activeLang;
    langSelect.disabled = false;

    populateVoiceDropdown(activeLang);
}

function populateVoiceDropdown(language) {
    voiceSelect.innerHTML = '';
    const models = availableModels[language] || [];

    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = model.name;
        voiceSelect.appendChild(option);
    });

    if (models.some(m => m.id === currentActiveModel)) {
        voiceSelect.value = currentActiveModel;
    }

    voiceSelect.disabled = false;
}

// Handle UI Dropdown changes
langSelect.addEventListener('change', (e) => {
    populateVoiceDropdown(e.target.value);
    triggerModelChange(voiceSelect.value);
});

voiceSelect.addEventListener('change', (e) => {
    triggerModelChange(e.target.value);
});

async function triggerModelChange(modelId) {
    if (modelId === currentActiveModel) return;

    // Set UI to loading state and resume polling
    setLoadingState(true, "Switching Model...");
    startPolling();

    try {
        await fetch(`${API_URL}/set_model`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model_id: modelId })
        });
        currentActiveModel = modelId;
    } catch (err) {
        console.error("Failed to change model", err);
    }
}

function setLoadingState(isLoading, badgeText = "Loading Model...") {
    if (isLoading) {
        statusBadge.textContent = badgeText;
        statusBadge.className = 'badge loading';
        textInput.disabled = true;
        speakBtn.disabled = true;
        deviceInfo.classList.remove('connected');
    } else {
        statusBadge.textContent = 'System Ready';
        statusBadge.className = 'badge ready';
        textInput.disabled = false;
        speakBtn.disabled = false;
        deviceInfo.classList.add('connected');
    }
}

// Poll backend status
async function checkStatus() {
    try {
        const res = await fetch(`${API_URL}/status`);
        const data = await res.json();

        if (data.status === 'ready') {
            setLoadingState(false);
            deviceInfo.textContent = `Output routed to device ID: ${data.device_id} | Active: ${data.active_model}`;
            stopPolling(); // Optimization: Stop spamming the backend once ready
        } else if (data.status === 'loading') {
            setLoadingState(true, "Loading Model...");
        } else if (data.status === 'error') {
            statusBadge.textContent = 'Model Error';
            statusBadge.className = 'badge error';
            stopPolling(); // Stop on error so we don't spam indefinitely
        }
    } catch (err) {
        // Backend not up yet
    }
}

// Polling controllers
function startPolling() {
    if (!pollInterval) {
        pollInterval = setInterval(checkStatus, 1000);
    }
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

// Initialization Sequence
fetchModels();
startPolling(); // Begin polling on startup

// Handle Speak Action
speakBtn.addEventListener('click', async () => {
    const text = textInput.value.trim();
    if (!text) return;

    speakBtn.disabled = true;
    textInput.disabled = true;
    btnText.textContent = 'Synthesizing...';
    loader.classList.remove('hidden');
    document.querySelector('.icon').classList.add('hidden');

    try {
        await fetch(`${API_URL}/speak`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
    } catch (err) {
        alert("Error sending request to backend.");
    } finally {
        speakBtn.disabled = false;
        textInput.disabled = false;
        btnText.textContent = 'Synthesize Speech';
        loader.classList.add('hidden');
        document.querySelector('.icon').classList.remove('hidden');
        textInput.focus();
    }
});

// Trigger speak on Ctrl+Enter
textInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter' && !speakBtn.disabled) {
        speakBtn.click();
    }
});