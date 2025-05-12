// Gemini Chat Integration for Floating Chat

class GeminiChatAPI {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.apiUrl = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent";
    }

    async generateResponse(message) {
        try {
            const response = await fetch(`${this.apiUrl}?key=${this.apiKey}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    contents: [
                        {
                            parts: [
                                {
                                    text: `Tu es un assistant spécialisé dans la réglementation de la pêche. \n\nQuestion de l'utilisateur: ${message}`
                                }
                            ]
                        }
                    ]
                })
            });

            if (!response.ok) {
                throw new Error(`Erreur API: ${response.status}`);
            }

            const data = await response.json();
            return data.candidates[0].content.parts[0].text;
        } catch (error) {
            console.error('Erreur lors de la génération de réponse:', error);
            return "Désolé, je n'ai pas pu générer une réponse. Veuillez réessayer plus tard.";
        }
    }
}

// Modification de la classe FloatingChat pour utiliser Gemini
document.addEventListener('DOMContentLoaded', () => {
    // Vérifier si FloatingChat existe déjà
    if (typeof FloatingChat !== 'undefined') {
        // Remplacer la classe FloatingChat existante
        class EnhancedFloatingChat extends FloatingChat {
            constructor() {
                super();
                // Initialiser l'API Gemini avec la clé fournie
                this.geminiAPI = new GeminiChatAPI("AIzaSyDU6Kv9Xnv7Zp1R4nPzyq3_36yYjVOgZFE");
                
                // Réinitialiser les écouteurs d'événements pour le bouton de chat
                const chatButton = document.getElementById('chat-button');
                if (chatButton) {
                    // Supprimer tous les écouteurs d'événements existants
                    const newChatButton = chatButton.cloneNode(true);
                    chatButton.parentNode.replaceChild(newChatButton, chatButton);
                    
                    // Ajouter un nouvel écouteur d'événement
                    newChatButton.addEventListener('click', () => this.toggleChat());
                }
            }

            // Surcharger la méthode sendMessage pour utiliser Gemini au lieu de l'API backend
            async sendMessage() {
                const inputField = document.getElementById('chat-input-field');
                const messagesContainer = document.getElementById('chat-messages');
                const message = inputField.value.trim();

                if (!message) return;

                // Ajouter le message de l'utilisateur
                this.addMessage(message, 'user');
                inputField.value = '';

                try {
                    // Afficher un indicateur de chargement
                    const loadingDiv = document.createElement('div');
                    loadingDiv.className = 'chat-message assistant-message';
                    loadingDiv.textContent = 'En train de réfléchir...';
                    messagesContainer.appendChild(loadingDiv);
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;

                    // Obtenir la réponse de Gemini
                    const response = await this.geminiAPI.generateResponse(message);
                    
                    // Remplacer l'indicateur de chargement par la réponse
                    messagesContainer.removeChild(loadingDiv);
                    this.addMessage(response, 'assistant');
                } catch (error) {
                    console.error('Erreur:', error);
                    this.addMessage('Désolé, une erreur est survenue. Veuillez réessayer.', 'assistant');
                }
            }
        }

        // Initialiser le chat amélioré au lieu du chat standard
        window.chatInstance = new EnhancedFloatingChat();
        console.log('Chat flottant Gemini initialisé');
    } else {
        console.error('FloatingChat n\'est pas défini. Assurez-vous que floating-chat.js est chargé avant gemini-chat.js');
    }
});