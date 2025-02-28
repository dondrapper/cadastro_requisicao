// Armazenar histórico de leituras
let barcodeHistory = [];
let streamlitDetected = false;
let currentMode = "auto"; // "auto", "login", "barcode"

// Elementos da interface
const statusElement = document.getElementById('connection-status');
const streamlitStatusElement = document.getElementById('streamlit-status');
const historyElement = document.getElementById('barcode-history');
const testButton = document.getElementById('test-connection');
const clearButton = document.getElementById('clear-history');
const modeSelect = document.getElementById('mode-select');

// Atualizar o status da conexão
function updateConnectionStatus(connected, message) {
    statusElement.className = connected ? 'status connected' : 'status disconnected';
    statusElement.textContent = message || (connected ? 'Conectado ao aplicativo nativo' : 'Desconectado');
}

// Atualizar o status do Streamlit
function updateStreamlitStatus(detected, tabId = null) {
    streamlitDetected = detected;
    
    if (detected) {
        streamlitStatusElement.textContent = "Aplicativo Streamlit detectado e pronto para receber códigos de barras";
        streamlitStatusElement.style.backgroundColor = "#d4edda";
        streamlitStatusElement.style.color = "#155724";
    } else {
        streamlitStatusElement.textContent = "Aplicativo Streamlit não detectado. Abra a página do sistema em uma aba.";
        streamlitStatusElement.style.backgroundColor = "#f8d7da";
        streamlitStatusElement.style.color = "#721c24";
    }
}

// Atualizar o histórico de leituras
function updateHistory() {
    if (barcodeHistory.length === 0) {
        historyElement.innerHTML = '<div class="code-item">Nenhum código lido ainda</div>';
        return;
    }
    
    historyElement.innerHTML = '';
    // Mostrar os códigos mais recentes primeiro
    for (let i = barcodeHistory.length - 1; i >= 0; i--) {
        const item = barcodeHistory[i];
        const element = document.createElement('div');
        element.className = 'code-item';
        element.textContent = `${item.code} (${new Date(item.timestamp).toLocaleTimeString()})`;
        historyElement.appendChild(element);
    }
}

// Verificar se há alguma aba com Streamlit aberta
function checkForStreamlit() {
    chrome.tabs.query({}, function(tabs) {
        let found = false;
        for (let tab of tabs) {
            // Verificar pela URL ou título se é uma página Streamlit
            if (tab.url && (
                tab.url.includes('streamlit') || 
                tab.url.includes('localhost:8501') ||
                (tab.title && tab.title.toLowerCase().includes('streamlit'))
            )) {
                found = true;
                updateStreamlitStatus(true, tab.id);
                break;
            }
        }
        
        if (!found) {
            updateStreamlitStatus(false);
        }
    });
}

// Verificar status da conexão
function checkConnection() {
    chrome.runtime.sendMessage({type: "check_connection"}, function(response) {
        if (response) {
            updateConnectionStatus(response.connected, response.message);
        } else {
            updateConnectionStatus(false, "Erro ao verificar conexão");
        }
    });
}

// Adicionar código ao histórico
function addToHistory(code) {
    if (!code) return;
    
    barcodeHistory.push({
        code: code,
        timestamp: Date.now()
    });
    
    // Limitar o histórico a 50 itens
    if (barcodeHistory.length > 50) {
        barcodeHistory.shift();
    }
    
    // Salvar no storage local
    chrome.storage.local.set({barcodeHistory: barcodeHistory});
    
    // Atualizar a interface
    updateHistory();
}

// Carregar histórico salvo
function loadSavedData() {
    chrome.storage.local.get(['barcodeHistory', 'scanMode'], function(data) {
        if (data.barcodeHistory) {
            barcodeHistory = data.barcodeHistory;
            updateHistory();
        }
        
        if (data.scanMode) {
            currentMode = data.scanMode;
            modeSelect.value = currentMode;
        }
    });
}

// Trocar o modo de escaneamento
function changeMode(mode) {
    currentMode = mode;
    chrome.storage.local.set({scanMode: mode});
    
    // Notificar todas as abas que o modo mudou
    chrome.tabs.query({}, function(tabs) {
        for (let tab of tabs) {
            try {
                chrome.tabs.sendMessage(tab.id, {
                    type: "mode_changed",
                    mode: mode
                });
            } catch (err) {
                // Ignorar erros para abas que não têm o content script
                console.log("Erro ao enviar para tab:", err);
            }
        }
    });
}

// Inicializar extensão
function initialize() {
    // Carregar dados salvos
    loadSavedData();
    
    // Verificar conexão
    checkConnection();
    
    // Verificar status do Streamlit
    checkForStreamlit();
}

// Escutar eventos de botão
testButton.addEventListener('click', function() {
    checkConnection();
    checkForStreamlit();
});

clearButton.addEventListener('click', function() {
    barcodeHistory = [];
    chrome.storage.local.remove('barcodeHistory');
    updateHistory();
});

// Escutar mudanças no modo de escaneamento
modeSelect.addEventListener('change', function() {
    changeMode(modeSelect.value);
});

// Escutar mensagens de código de barras e outras mensagens
chrome.runtime.onMessage.addListener(function(message) {
    console.log("Mensagem recebida no popup:", message);
    
    if (message.type === 'barcode_scanned') {
        addToHistory(message.code || message.data);
    } 
    else if (message.type === 'streamlit_status') {
        updateStreamlitStatus(message.detected);
    }
});

// Inicializar quando o documento estiver carregado
document.addEventListener('DOMContentLoaded', initialize);

// Verificar Streamlit periodicamente
setInterval(checkForStreamlit, 5000);