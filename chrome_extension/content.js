// Variáveis para controle da captura do código de barras
let barcodeBuffer = '';
let lastKeyTime = 0;
let barcodeTimer = null;
const MAX_DELAY = 100;  // Tempo máximo entre caracteres (ms)
const SUBMIT_DELAY = 50;  // Tempo reduzido para envio automático (ms)
const END_CHAR = 'Enter';  // Caractere que indica fim da leitura
let currentMode = "auto"; // Modo de captura: "auto", "login", "barcode"

// Detectar se estamos em uma página Streamlit
function isStreamlitPage() {
    return document.querySelector('iframe[title="streamlit_app"]') !== null ||
           document.querySelector('div[data-testid="stToolbar"]') !== null ||
           document.querySelector('div[data-testid="stHeader"]') !== null ||
           window.location.hostname.includes('streamlit') ||
           (window.location.hostname === 'localhost' && window.location.port === '8501');
}

// Encontrar elementos de input no Streamlit
function findStreamlitInputs() {
    // Buscar todos os inputs visíveis
    const inputs = Array.from(document.querySelectorAll('input[type="text"]:not([disabled]):not([readonly])'));
    
    // Se não encontrou inputs, retornar objeto vazio
    if (inputs.length === 0) {
        return { login: null, barcode: null };
    }
    
    // Se estamos no modo "login", usar o primeiro input
    if (currentMode === "login" && inputs.length > 0) {
        return { login: inputs[0], barcode: null };
    }
    
    // Se estamos no modo "barcode", usar o primeiro input (ou o segundo se houver)
    if (currentMode === "barcode") {
        return { login: null, barcode: inputs.length > 1 ? inputs[1] : inputs[0] };
    }
    
    // No modo automático, tentar classificar ou usar posição
    // Primeiro input geralmente é login, segundo é código de barras
    if (inputs.length === 1) {
        return { login: inputs[0], barcode: inputs[0] };
    } else if (inputs.length >= 2) {
        return { login: inputs[0], barcode: inputs[1] };
    }
    
    return { login: null, barcode: null };
}

// Simular pressionar Enter em um elemento
function simulateEnterPress(element) {
    if (!element) return false;
    
    // Primeiro, enviar um evento keydown
    const keydownEvent = new KeyboardEvent('keydown', {
        key: 'Enter',
        code: 'Enter',
        keyCode: 13,
        which: 13,
        bubbles: true,
        cancelable: true
    });
    const keydownResult = element.dispatchEvent(keydownEvent);
    
    // Depois, enviar um evento keypress
    const keypressEvent = new KeyboardEvent('keypress', {
        key: 'Enter',
        code: 'Enter',
        keyCode: 13,
        which: 13,
        bubbles: true,
        cancelable: true
    });
    const keypressResult = element.dispatchEvent(keypressEvent);
    
    // Por fim, enviar um evento keyup
    const keyupEvent = new KeyboardEvent('keyup', {
        key: 'Enter',
        code: 'Enter',
        keyCode: 13,
        which: 13,
        bubbles: true,
        cancelable: true
    });
    const keyupResult = element.dispatchEvent(keyupEvent);
    
    // Tentar também submeter o formulário, se existir
    let form = element.closest('form');
    if (form) {
        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    }
    
    return keydownResult && keypressResult && keyupResult;
}

// Enviar código de barras para a página Streamlit
function sendToStreamlit(barcode) {
    if (!isStreamlitPage()) return;
    
    console.log('Tentando injetar código:', barcode, 'Modo:', currentMode);
    
    // Encontrar os inputs de Streamlit
    const inputs = findStreamlitInputs();
    
    // Identificar qual input usar com base no modo atual
    let targetInput = null;
    if (currentMode === "login") {
        targetInput = inputs.login;
    } else if (currentMode === "barcode") {
        targetInput = inputs.barcode;
    } else { // Modo automático
        // Tentar determinar automaticamente com base no tamanho do código
        if (barcode.length <= 11) {
            targetInput = inputs.login; // Códigos menores geralmente são crachás
        } else {
            targetInput = inputs.barcode; // Códigos maiores são provavelmente códigos de barras
        }
    }
    
    // Se encontrou um alvo, injetar o código
    if (targetInput) {
        // Focar no input
        targetInput.focus();
        
        // Limpar valor existente
        targetInput.value = '';
        
        // Definir o novo valor
        targetInput.value = barcode;
        
        // Disparar eventos necessários para que o Streamlit detecte a mudança
        targetInput.dispatchEvent(new Event('input', { bubbles: true }));
        targetInput.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Simular pressionar Enter após um pequeno atraso
        // Este atraso é importante para dar tempo do Streamlit processar o valor
        setTimeout(() => {
            simulateEnterPress(targetInput);
            
            // Segundo método de simulação de Enter - ativar botões próximos
            // Tentar encontrar botões de submissão próximos
            const buttons = document.querySelectorAll('button:not([disabled])');
            let submitButton = null;
            
            // Procurar por botões que parecem ser de submissão
            for (const button of buttons) {
                if (button.textContent.toLowerCase().includes('enviar') || 
                    button.textContent.toLowerCase().includes('submit') ||
                    button.type === 'submit') {
                    submitButton = button;
                    break;
                }
            }
            
            // Se encontrou um botão que parece de submissão, clique nele
            if (submitButton) {
                submitButton.click();
            }
            
            console.log('Simulação de ENTER realizada');
        }, 200); // Atraso maior para dar tempo ao Streamlit processar
        
        console.log('Código injetado com sucesso no campo:', targetInput);
    } else {
        console.log('Não foi possível encontrar um campo para injetar o código');
    }
    
    // Enviar mensagem para a janela atual (para possíveis scripts da página)
    window.postMessage({
        type: 'barcode_data',
        data: barcode,
        source: 'barcode_extension'
    }, '*');
}

// Escuta eventos de teclado
document.addEventListener('keydown', function(event) {
    const currentTime = new Date().getTime();
    
    // Verificar se pode ser parte de uma leitura de código de barras
    if (currentTime - lastKeyTime > MAX_DELAY) {
        barcodeBuffer = '';  // Resetar o buffer se passou muito tempo
    }
    
    lastKeyTime = currentTime;
    
    // Se for a tecla de fim da leitura (Enter) ou qualquer caractere de um código de barras
    if (event.key === END_CHAR || (event.key.length === 1 && /[\d]/.test(event.key))) {
        // Se for Enter ou um dígito, adiciona ao buffer
        if (event.key === END_CHAR) {
            // Prevenir comportamento padrão do Enter em páginas Streamlit apenas se temos algo no buffer
            if (isStreamlitPage() && barcodeBuffer.length > 0) {
                event.preventDefault();
            }
        } else if (event.key.length === 1) {
            // Adicionar caractere ao buffer (apenas caracteres simples)
            barcodeBuffer += event.key;
        }
        
        // Limpar qualquer timer anterior
        if (barcodeTimer) {
            clearTimeout(barcodeTimer);
        }
        
        // Configurar um timer para envio automático se estamos em página Streamlit
        if (isStreamlitPage()) {
            barcodeTimer = setTimeout(() => {
                // Verificar se o buffer tem conteúdo suficiente e/ou se Enter foi pressionado
                const isValidBarcode = (barcodeBuffer.length >= 3);
                
                // Enviar código se Enter foi pressionado (com código no buffer) ou
                // se o código tem tamanho suficiente (típico de leitores automáticos)
                const shouldSubmit = (isValidBarcode && event.key === END_CHAR) || 
                                      (barcodeBuffer.length >= 11 && barcodeBuffer.length <= 13);
                
                if (shouldSubmit) {
                    console.log('Enviando código automaticamente:', barcodeBuffer);
                    
                    // Enviar para o script de background
                    chrome.runtime.sendMessage({
                        type: "barcode_scanned",
                        data: barcodeBuffer
                    });
                    
                    // Enviar para Streamlit
                    sendToStreamlit(barcodeBuffer);
                    
                    // Limpar o buffer
                    barcodeBuffer = '';
                } else if (event.key === END_CHAR && barcodeBuffer.length > 0) {
                    // Se o Enter foi pressionado mas o código é muito curto,
                    // pode ser uma entrada manual, então resetamos o buffer
                    barcodeBuffer = '';
                }
                
                barcodeTimer = null;
            }, SUBMIT_DELAY);
        }
    }
});

// Escuta mensagens do script de background
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
    console.log("Mensagem recebida no content:", message);
    
    if (message.type === "processed_barcode") {
        // Se estivermos em uma página Streamlit, enviar resultado processado
        if (isStreamlitPage()) {
            sendToStreamlit(message.data.original_code);
        }
    }
    else if (message.type === "mode_changed") {
        currentMode = message.mode;
        console.log("Modo de leitura alterado para:", currentMode);
    }
    
    // Sempre retorne true se você pretende responder assincronamente
    return true;
});

// Adicionar listener para mensagens da página
window.addEventListener('message', function(event) {
    // Verificar se a mensagem veio da nossa extensão para evitar loops
    if (event.data && event.data.type === 'barcode_request' && event.data.source !== 'barcode_extension') {
        // Página solicitando código de barras (pode ser usado para interação futura)
        console.log('Página solicitou leitura de código de barras');
    }
}, false);

// Carregar modo atual
chrome.storage.local.get('scanMode', function(data) {
    if (data.scanMode) {
        currentMode = data.scanMode;
        console.log("Modo carregado:", currentMode);
    }
});

// Executar verificação e notificação inicial
(function init() {
    // Verificar se estamos em uma página Streamlit
    const streamlitDetected = isStreamlitPage();
    console.log("Streamlit detectado:", streamlitDetected);
    
    // Informar que o script de conteúdo foi carregado
    chrome.runtime.sendMessage({
        type: "content_loaded", 
        url: window.location.href,
        isStreamlit: streamlitDetected
    });
    
    // Se for uma página Streamlit, notificar especificamente
    if (streamlitDetected) {
        chrome.runtime.sendMessage({
            type: "streamlit_detected", 
            url: window.location.href
        });
        console.log("Página Streamlit detectada, scanner de código de barras ativado");
    }
})();