// UI Chatbot - Bulle flottante pour l'assistance contextuelle

document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si les variables CSS nécessaires sont définies
    const checkCSSVariables = () => {
        const root = getComputedStyle(document.documentElement);
        const accentColor = root.getPropertyValue('--accent-color').trim();
        const secondaryColor = root.getPropertyValue('--secondary-color').trim();
        
        if (!accentColor || !secondaryColor) {
            console.warn('Variables CSS manquantes pour le chatbot. Utilisation des valeurs par défaut.');
            // Définir des valeurs par défaut si nécessaire
            document.documentElement.style.setProperty('--accent-color', '#38ada9');
            document.documentElement.style.setProperty('--secondary-color', '#079992');
        }
    };
    
    checkCSSVariables();
    
    // Créer la bulle de chat flottante avec un délai pour s'assurer que tout est chargé
    setTimeout(() => {
        createChatBubble();
    }, 500); // Augmenté à 500ms pour s'assurer que tout est bien chargé

    // Initialiser les variables
    let chatOpen = false;
    let messages = [];
    const maxMessages = 50; // Limiter le nombre de messages stockés

    // Fonction pour créer la bulle de chat et l'interface
    function createChatBubble() {
        // Supprimer toute instance existante pour éviter les doublons
        const existingContainer = document.querySelector('.ui-chatbot-container');
        if (existingContainer) {
            document.body.removeChild(existingContainer);
        }
        
        // Créer le conteneur principal
        const chatContainer = document.createElement('div');
        chatContainer.className = 'ui-chatbot-container';
        document.body.appendChild(chatContainer);

        // Créer la bulle flottante
        const chatBubble = document.createElement('div');
        chatBubble.className = 'ui-chatbot-bubble';
        chatBubble.innerHTML = '<i class="fas fa-comment-dots"></i>';
        chatContainer.appendChild(chatBubble);
        
        // S'assurer que la bulle est visible et cliquable
        chatBubble.style.display = 'flex';
        chatBubble.style.cursor = 'pointer';
        console.log('Chat bubble created');

        // Créer l'interface de chat (initialement cachée)
        const chatInterface = document.createElement('div');
        chatInterface.className = 'ui-chatbot-interface';
        chatInterface.style.display = 'none';
        chatContainer.appendChild(chatInterface);

        // En-tête du chat
        const chatHeader = document.createElement('div');
        chatHeader.className = 'ui-chatbot-header';
        chatHeader.innerHTML = `
            <div class="ui-chatbot-title">
                <i class="fas fa-robot"></i>
                <span>Assistant GuidMarine</span>
            </div>
            <div class="ui-chatbot-close">
                <i class="fas fa-times"></i>
            </div>
        `;
        chatInterface.appendChild(chatHeader);

        // Zone des messages
        const chatMessages = document.createElement('div');
        chatMessages.className = 'ui-chatbot-messages';
        chatInterface.appendChild(chatMessages);

        // Message de bienvenue
        addMessage(chatMessages, 'Bonjour ! Je suis votre assistant GuidMarine. Comment puis-je vous aider à naviguer dans l\'application ?', 'assistant');

        // Zone de saisie
        const chatInput = document.createElement('div');
        chatInput.className = 'ui-chatbot-input';
        chatInput.innerHTML = `
            <input type="text" placeholder="Posez votre question..." />
            <button><i class="fas fa-paper-plane"></i></button>
        `;
        chatInterface.appendChild(chatInput);

        // Événements avec capture explicite pour éviter les problèmes de propagation
        chatBubble.addEventListener('click', function(e) {
            console.log('Bulle cliquée');
            openChat();
            e.preventDefault();
            e.stopPropagation();
        }, true);
        
        chatHeader.querySelector('.ui-chatbot-close').addEventListener('click', function(e) {
            console.log('Bouton fermer cliqué');
            closeChat();
            e.preventDefault();
            e.stopPropagation();
        }, true);
        
        const inputField = chatInput.querySelector('input');
        const sendButton = chatInput.querySelector('button');
        
        sendButton.addEventListener('click', () => sendMessage(inputField, chatMessages));
        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage(inputField, chatMessages);
            }
        });
        
        // Fonctions pour ouvrir et fermer le chat séparément pour plus de robustesse
        function openChat() {
            chatOpen = true;
            console.log('Opening chat interface');
            
            chatInterface.style.display = 'flex';
            chatBubble.style.display = 'none';
            
            // S'assurer que l'interface est visible
            chatInterface.style.opacity = '1';
            chatInterface.style.visibility = 'visible';
            
            // Focus sur le champ de saisie
            setTimeout(() => {
                const inputElement = chatContainer.querySelector('.ui-chatbot-input input');
                if (inputElement) {
                    inputElement.focus();
                    console.log('Input field focused');
                }
            }, 100);
        }
        
        function closeChat() {
            chatOpen = false;
            console.log('Closing chat interface');
            
            chatInterface.style.display = 'none';
            chatBubble.style.display = 'flex';
        }
    }

    // Fonction pour ajouter un message à l'interface
    function addMessage(container, text, sender) {
        const messageElement = document.createElement('div');
        messageElement.className = `ui-chatbot-message ${sender}-message`;
        
        // Convertir les liens markdown en HTML
        const formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/- (.*?)\n/g, '<li>$1</li>');
        
        messageElement.innerHTML = formattedText;
        container.appendChild(messageElement);
        
        // Faire défiler vers le bas
        container.scrollTop = container.scrollHeight;
        
        // Stocker le message
        messages.push({ text, sender });
        if (messages.length > maxMessages) {
            messages.shift();
        }
    }

    // Fonction pour envoyer un message
    function sendMessage(inputField, chatMessages) {
        const message = inputField.value.trim();
        if (message) {
            // Afficher le message de l'utilisateur
            addMessage(chatMessages, message, 'user');
            inputField.value = '';
            
            // Afficher l'indicateur de chargement
            const loadingElement = document.createElement('div');
            loadingElement.className = 'ui-chatbot-message assistant-message loading';
            loadingElement.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
            chatMessages.appendChild(loadingElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Envoyer la requête au serveur
            fetch('/api/ui-chatbot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            })
            .then(response => response.json())
            .then(data => {
                // Supprimer l'indicateur de chargement
                chatMessages.removeChild(loadingElement);
                
                // Afficher la réponse
                addMessage(chatMessages, data.text, 'assistant');
            })
            .catch(error => {
                // Supprimer l'indicateur de chargement
                chatMessages.removeChild(loadingElement);
                
                // Afficher un message d'erreur
                addMessage(chatMessages, "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer.", 'assistant');
                console.error('Error:', error);
            });
        }
    }
});