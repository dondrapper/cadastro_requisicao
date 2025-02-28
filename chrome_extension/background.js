// Variáveis de estado
let streamlitTabs = new Set();

// Função para detectar abas Streamlit
function detectStreamlitTabs() {
    chrome.tabs.query({}, function(tabs) {
        const oldCount = streamlitTabs.size;
        streamlitTabs.clear();
        
        for (let tab of tabs) {
            // Verificar se é uma página Streamlit
            if (tab.url && (
                tab.url.includes('streamlit') || 
                tab.url.includes('localhost:8501') ||
                (tab.title && tab.title.toLowerCase().includes('streamlit'))
            )) {
                streamlitTabs.add(tab.id);
            }
        }
        
        // Notificar popup se o estado mudou
        if (oldCount === 0 && streamlitTabs.size > 0) {
            notifyStreamlitDetected(true);
        } else if (oldCount > 0 && streamlitTabs.size === 0) {
            notifyStreamlitDetected(false);
        }
    });
}

// Notificar que o Streamlit foi detectado
function notifyStreamlitDetected(detected) {
    chrome.runtime.sendMessage({
        type: "streamlit_status",
        detected: detected
    });
}

// Escutar mensagens dos scripts de conteúdo
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
    console.log("Mensagem recebida no background:", message);
    
    // Verificar tipo de mensagem
    if (message.type === "barcode_scanned") {
        // Notificar o popup
        chrome.runtime.sendMessage({
            type: "barcode_scanned",
            code: message.data
        });
        
        // Enviar para todas as abas Streamlit conhecidas
        streamlitTabs.forEach(tabId => {
            try {
                chrome.tabs.sendMessage(tabId, {
                    type: "processed_barcode",
                    data: { original_code: message.data }
                });
            } catch (error) {
                console.error("Erro ao enviar mensagem para tab:", error);
            }
        });
        
        sendResponse({status: "received"});
    } 
    else if (message.type === "check_connection") {
        sendResponse({
            connected: true,
            message: "Extensão funcionando corretamente"
        });
    }
    else if (message.type === "content_loaded" || message.type === "streamlit_detected") {
        // Verificar se é uma aba Streamlit
        if (sender.tab && (message.isStreamlit || 
                         (message.url && (message.url.includes('streamlit') || 
                                        message.url.includes('localhost:8501'))))) {
            streamlitTabs.add(sender.tab.id);
            notifyStreamlitDetected(true);
        }
        
        sendResponse({status: "acknowledged"});
    }
    else if (message.type === "check_streamlit") {
        // Forçar nova verificação das abas
        detectStreamlitTabs();
    }
    
    return true; // Manter o canal aberto para resposta assíncrona
});

// Inicializar a extensão
function init() {
    console.log("Inicializando background script");
    
    // Detectar abas Streamlit
    detectStreamlitTabs();
    
    // Configurar verificação periódica
    setInterval(detectStreamlitTabs, 5000);
}

// Monitorar alterações nas abas
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete') {
        detectStreamlitTabs();
    }
});

chrome.tabs.onRemoved.addListener((tabId) => {
    if (streamlitTabs.has(tabId)) {
        streamlitTabs.delete(tabId);
        if (streamlitTabs.size === 0) {
            notifyStreamlitDetected(false);
        }
    }
});

// Iniciar a extensão
init();