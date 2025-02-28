// Variáveis para controle da captura do código de barras
let barcodeBuffer = '';
let lastKeyTime = 0;
let barcodeTimer = null;
const MAX_DELAY = 100;  // Tempo máximo entre caracteres (ms)
const SUBMIT_DELAY = 300;  // Tempo para envio automático após último caractere (ms)
const END_CHAR = 'Enter';  // Caractere que indica fim da leitura

// Detectar se estamos em uma página Streamlit
function isStreamlitPage() {
    return document.querySelector('iframe[title="streamlit_app"]') !== null ||
           document.querySelector('div[data-testid="stToolbar"]') !== null ||
           window.location.hostname.includes('streamlit');
}

// Enviar código de barras para a página Streamlit
function sendToStreamlit(barcode) {
    // Enviar mensagem para a janela atual
    window.postMessage({
        type: 'barcode_data',
        data: barcode,
        source: 'barcode_extension'
    }, '*');
    
    console.log('Código de barras enviado para Streamlit:', barcode);
}

// Escuta eventos de teclado
document.addEventListener('keydown', function(event) {
    const currentTime = new Date().getTime();
    
    // Verificar se pode ser parte de uma leitura de código de barras
    if (currentTime - lastKeyTime > MAX_DELAY) {
        barcodeBuffer = '';  // Resetar o buffer se passou muito tempo
    }
    
    lastKeyTime = currentTime;
    
    // Se for a tecla de fim da leitura (normalmente Enter) ou se passou um tempo desde o último caractere
    if (event.key === END_CHAR || (currentTime - lastKeyTime > MAX_DELAY && barcodeBuffer.length > 3)) {
        if (barcodeBuffer.length > 3) {  // Verificar se tem tamanho mínimo para ser um código
            // Primeiro enviar para o script de background (funcionamento original)
            chrome.runtime.sendMessage({
                type: "barcode_scanned",
                data: barcodeBuffer
            });
            
            // Se estivermos em uma página Streamlit, enviar para ela também
            if (isStreamlitPage()) {
                sendToStreamlit(barcodeBuffer);
            }
            
            // Limpar o buffer
            barcodeBuffer = '';
            
            // Se estivermos em uma página Streamlit e for a tecla Enter, prevenir o comportamento padrão
            // para evitar submissão de formulário ou outras ações
            if (isStreamlitPage() && event.key === END_CHAR) {
                event.preventDefault();
            }
        }
    } else if (event.key.length === 1) {
        // Adicionar caractere ao buffer (apenas caracteres simples)
        barcodeBuffer += event.key;
        
        // Limpar qualquer timer anterior
        if (barcodeTimer) {
            clearTimeout(barcodeTimer);
        }
        
        // Se estamos em uma página Streamlit, configurar um timer para envio automático
        if (isStreamlitPage()) {
            barcodeTimer = setTimeout(() => {
                // Se o buffer ainda tem conteúdo, enviar automaticamente
                if (barcodeBuffer.length > 3) {
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
                }
                barcodeTimer = null;
            }, SUBMIT_DELAY);
        }
    }
});

// Escuta mensagens do script de background
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
    if (message.type === "processed_barcode") {
        // Se estivermos em uma página Streamlit, enviar resultado processado
        if (isStreamlitPage()) {
            sendToStreamlit(message.data.original_code);
        }
        
        // Aqui você pode mostrar alguma indicação visual na página
        console.log("Código de barras processado:", message.data);
    }
    
    // Sempre retorne true se você pretende responder assincronamente
    return true;
});

// Informar que o script de conteúdo foi carregado
chrome.runtime.sendMessage({type: "content_loaded", url: window.location.href});

// Adicionar listener para mensagens da página
window.addEventListener('message', function(event) {
    // Verificar se a mensagem veio da nossa extensão para evitar loops
    if (event.data && event.data.type === 'barcode_request' && event.data.source !== 'barcode_extension') {
        // Página solicitando código de barras (pode ser usado para interação futura)
        console.log('Página solicitou leitura de código de barras');
    }
}, false);