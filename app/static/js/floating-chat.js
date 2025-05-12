// Floating Chat Component
class FloatingChat {
    constructor() {
        this.isChatOpen = false;
        this.createChatElement();
        this.initializeEventListeners();
    }

    createChatElement() {
        // Create chat container
        const chatContainer = document.createElement('div');
        chatContainer.id = 'floating-chat';
        chatContainer.innerHTML = `
            <div class="chat-button" id="chat-button">
                <i class="bi bi-chat-dots"></i>
            </div>
            <div class="chat-box" id="chat-box">
                <div class="chat-header">
                    <h5>Assistant Réglementaire</h5>
                    <button class="close-chat" id="close-chat">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
                <div class="chat-messages" id="chat-messages"></div>
                <div class="chat-input">
                    <textarea id="chat-input-field" placeholder="Posez votre question..."></textarea>
                    <button id="send-message">
                        <i class="bi bi-send"></i>
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(chatContainer);

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            #floating-chat {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
                font-family: 'Inter', sans-serif;
            }

            .chat-button {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: #8B4513;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15), 0 0 0 2px rgba(205, 133, 63, 0.5);
                transition: all 0.3s ease;
                z-index: 1050;
                position: relative;
            }

            .chat-button i {
                color: white;
                font-size: 24px;
            }

            .chat-button:hover {
                transform: scale(1.1);
                background: #A0522D;
            }

            .chat-box {
                display: none;
                position: fixed;
                bottom: 90px;
                right: 20px;
                width: 350px;
                height: 500px;
                background: linear-gradient(135deg, rgba(30, 20, 10, 0.95), rgba(50, 30, 20, 0.95));
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(205, 133, 63, 0.2);
            }

            .chat-header {
                padding: 15px;
                background: rgba(30, 30, 30, 0.9);
                color: #CD853F;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }

            .chat-header h5 {
                margin: 0;
                font-weight: 600;
            }

            .close-chat {
                background: none;
                border: none;
                color: #CD853F;
                cursor: pointer;
                padding: 5px;
            }

            .close-chat:hover {
                color: #DEB887;
            }

            .chat-messages {
                height: 370px;
                padding: 15px;
                overflow-y: auto;
                color: #ffffff;
            }

            .chat-message {
                margin-bottom: 15px;
                max-width: 80%;
                padding: 10px 15px;
                border-radius: 15px;
                line-height: 1.4;
            }

            .user-message {
                background: rgba(205, 133, 63, 0.2);
                margin-left: auto;
                border-bottom-right-radius: 5px;
            }

            .assistant-message {
                background: rgba(255, 255, 255, 0.1);
                margin-right: auto;
                border-bottom-left-radius: 5px;
            }

            .chat-input {
                padding: 15px;
                background: rgba(30, 30, 30, 0.9);
                display: flex;
                gap: 10px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }

            #chat-input-field {
                flex: 1;
                padding: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 5px;
                background: rgba(50, 50, 50, 0.9);
                color: white;
                resize: none;
                height: 40px;
                line-height: 20px;
            }

            #chat-input-field:focus {
                outline: none;
                border-color: #CD853F;
            }

            #send-message {
                width: 40px;
                height: 40px;
                border: none;
                border-radius: 5px;
                background: #8B4513;
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }

            #send-message:hover {
                background: #A0522D;
            }

            @media (max-width: 480px) {
                .chat-box {
                    width: 90%;
                    right: 5%;
                    left: 5%;
                }
            }
        `;
        document.head.appendChild(style);
    }

    initializeEventListeners() {
        const chatButton = document.getElementById('chat-button');
        const chatBox = document.getElementById('chat-box');
        const closeChat = document.getElementById('close-chat');
        const sendButton = document.getElementById('send-message');
        const inputField = document.getElementById('chat-input-field');
        const messagesContainer = document.getElementById('chat-messages');

        chatButton.addEventListener('click', () => this.toggleChat());
        closeChat.addEventListener('click', () => this.toggleChat());
        
        sendButton.addEventListener('click', () => this.sendMessage());
        
        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    toggleChat() {
        const chatBox = document.getElementById('chat-box');
        this.isChatOpen = !this.isChatOpen;
        chatBox.style.display = this.isChatOpen ? 'block' : 'none';
    }

    async sendMessage() {
        const inputField = document.getElementById('chat-input-field');
        const messagesContainer = document.getElementById('chat-messages');
        const message = inputField.value.trim();

        if (!message) return;

        // Add user message
        this.addMessage(message, 'user');
        inputField.value = '';

        try {
            // Send message to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `message=${encodeURIComponent(message)}`
            });

            if (!response.ok) throw new Error('Erreur réseau');

            const data = await response.json();
            
            // Add assistant response
            this.addMessage(data.response || data.message, 'assistant');
        } catch (error) {
            console.error('Erreur:', error);
            this.addMessage('Désolé, une erreur est survenue. Veuillez réessayer.', 'assistant');
        }
    }

    addMessage(text, type) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}-message`;
        messageDiv.textContent = text;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Vérifier si le chat n'a pas déjà été initialisé par gemini-chat.js
    if (!window.chatInstance) {
        window.chatInstance = new FloatingChat();
        console.log('Chat flottant standard initialisé');
    }
});