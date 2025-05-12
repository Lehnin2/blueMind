/**
 * Script principal pour l'assistant intelligent
 * Gère les interactions utilisateur et l'intégration avec l'API
 */

document.addEventListener('DOMContentLoaded', function() {
    // Éléments du DOM
    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const exportChatBtn = document.getElementById('exportChatBtn');
    const voiceInputBtn = document.getElementById('voiceInputBtn');
    const uploadPdfBtn = document.getElementById('uploadPdfBtn');
    const suggestionChips = document.querySelectorAll('.suggestion-chip');
    const agentOptions = document.querySelectorAll('.agent-option');
    
    // État de l'application
    let currentAgent = 'llama4';
    let isProcessing = false;
    
    // Initialiser l'interface
    initializeUI();
    
    // Fonction pour initialiser l'interface utilisateur
    function initializeUI() {
        // Configurer les écouteurs d'événements
        sendButton.addEventListener('click', handleSendMessage);
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        });
        
        // Configurer les écouteurs pour les puces de suggestion
        suggestionChips.forEach(chip => {
            chip.addEventListener('click', function() {
                messageInput.value = this.textContent;
                messageInput.focus();
            });
        });
        
        // Configurer les écouteurs pour les options d'agent
        agentOptions.forEach(option => {
            option.addEventListener('click', function() {
                // Supprimer la classe active de toutes les options
                agentOptions.forEach(opt => opt.classList.remove('active'));
                // Ajouter la classe active à l'option sélectionnée
                this.classList.add('active');
                // Mettre à jour l'agent actuel
                currentAgent = this.dataset.agent;
                // Ajouter un message système indiquant le changement d'agent
                addSystemMessage(`Agent changé pour: ${this.querySelector('.agent-option-title').textContent}`);
            });
        });
        
        // Configurer les boutons d'action
        clearChatBtn.addEventListener('click', clearChat);
        exportChatBtn.addEventListener('click', exportChat);
        voiceInputBtn.addEventListener('click', toggleVoiceInput);
        uploadPdfBtn.addEventListener('click', togglePdfUpload);
        
        // Ajuster automatiquement la hauteur du textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
    
    // Fonction pour gérer l'envoi d'un message
    async function handleSendMessage() {
        const message = messageInput.value.trim();
        if (message === '' || isProcessing) return;
        
        // Ajouter le message de l'utilisateur au chat
        addUserMessage(message);
        
        // Réinitialiser l'input
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Empêcher l'envoi de plusieurs messages simultanés
        isProcessing = true;
        
        try {
            // Vérifier si la requête nécessite une recherche web
            if (window.DeepSearch && window.DeepSearch.needsWebSearch(message)) {
                // Effectuer une recherche web
                const searchResult = await window.DeepSearch.performWebSearch(message);
                window.DeepSearch.addWebSearchMessage(searchResult);
            } else {
                // Traitement normal de la requête
                await processQuery(message);
            }
        } catch (error) {
            console.error('Erreur lors du traitement du message:', error);
            addBotMessage('Désolé, une erreur est survenue lors du traitement de votre demande.');
        } finally {
            isProcessing = false;
        }
    }
    
    // Fonction pour traiter une requête via l'API
    async function processQuery(query) {
        try {
            // Afficher l'indicateur de saisie
            showTypingIndicator();
            
            // Préparer les données pour la requête
            const formData = new FormData();
            formData.append('message', query);
            formData.append('agent', currentAgent);
            
            // Envoyer la requête à l'API
            const response = await fetch('/api/chat', {
                method: 'POST',
                body: formData
            });
            
            // Vérifier si la requête a réussi
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            
            // Analyser la réponse JSON
            const data = await response.json();
            
            // Masquer l'indicateur de saisie
            hideTypingIndicator();
            
            // Ajouter la réponse au chat
            addBotMessage(data.response);
            
            // Mettre à jour les suggestions si disponibles
            if (data.suggestions && data.suggestions.length > 0) {
                updateSuggestions(data.suggestions);
            }
        } catch (error) {
            // Masquer l'indicateur de saisie en cas d'erreur
            hideTypingIndicator();
            
            console.error('Erreur lors du traitement de la requête:', error);
            addBotMessage('Désolé, une erreur est survenue lors du traitement de votre demande.');
        }
    }
    
    // Fonction pour ajouter un message utilisateur au chat
    function addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">${escapeHtml(message)}</div>
            <div class="message-time">Aujourd'hui, ${timeString}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Fonction pour ajouter un message du bot au chat
    function addBotMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Convertir les liens en éléments cliquables
        const formattedMessage = formatMessage(message);
        
        messageDiv.innerHTML = `
            <div class="message-content">${formattedMessage}</div>
            <div class="message-time">Aujourd'hui, ${timeString}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Fonction pour ajouter un message système au chat
    function addSystemMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system-message';
        messageDiv.style.alignSelf = 'center';
        messageDiv.style.background = 'rgba(0, 0, 0, 0.3)';
        messageDiv.style.color = 'rgba(255, 255, 255, 0.7)';
        messageDiv.style.fontSize = '0.9rem';
        messageDiv.style.padding = '8px 12px';
        messageDiv.style.borderRadius = '10px';
        
        messageDiv.innerHTML = `<div class="message-content">${escapeHtml(message)}</div>`;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Fonction pour afficher l'indicateur de saisie
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = `
            <span>Assistant est en train d'écrire</span>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Fonction pour masquer l'indicateur de saisie
    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Fonction pour mettre à jour les suggestions
    function updateSuggestions(suggestions) {
        const suggestionsContainer = document.querySelector('.suggestions');
        if (!suggestionsContainer) return;
        
        // Vider le conteneur de suggestions
        suggestionsContainer.innerHTML = '';
        
        // Ajouter les nouvelles suggestions
        suggestions.forEach(suggestion => {
            const chip = document.createElement('div');
            chip.className = 'suggestion-chip';
            chip.textContent = suggestion;
            chip.addEventListener('click', () => {
                messageInput.value = suggestion;
                messageInput.focus();
            });
            
            suggestionsContainer.appendChild(chip);
        });
    }
    
    // Fonction pour effacer le chat
    function clearChat() {
        // Garder uniquement le message de bienvenue
        const welcomeMessage = chatMessages.querySelector('.message');
        chatMessages.innerHTML = '';
        if (welcomeMessage) {
            chatMessages.appendChild(welcomeMessage);
        }
        
        // Ajouter un message système
        addSystemMessage('Conversation effacée');
    }
    
    // Fonction pour exporter le chat
    function exportChat() {
        // Récupérer tous les messages
        const messages = chatMessages.querySelectorAll('.message');
        let chatContent = 'Conversation avec l\'Assistant Réglementaire\n\n';
        
        messages.forEach(message => {
            const content = message.querySelector('.message-content').textContent;
            const time = message.querySelector('.message-time')?.textContent || '';
            
            if (message.classList.contains('user-message')) {
                chatContent += `Vous (${time}): ${content}\n\n`;
            } else if (message.classList.contains('bot-message')) {
                chatContent += `Assistant (${time}): ${content}\n\n`;
            } else if (message.classList.contains('system-message')) {
                chatContent += `[Système] ${content}\n\n`;
            }
        });
        
        // Créer un blob et un lien de téléchargement
        const blob = new Blob([chatContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation_${new Date().toISOString().slice(0, 10)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        // Ajouter un message système
        addSystemMessage('Conversation exportée');
    }
    
    // Fonction pour activer/désactiver l'enregistrement vocal
    function toggleVoiceInput() {
        const voiceRecordingContainer = document.getElementById('voiceRecordingContainer');
        if (voiceRecordingContainer.style.display === 'none') {
            voiceRecordingContainer.style.display = 'flex';
            // Logique d'enregistrement vocal à implémenter
        } else {
            voiceRecordingContainer.style.display = 'none';
        }
    }
    
    // Fonction pour activer/désactiver l'upload de PDF
    function togglePdfUpload() {
        const pdfUploadModal = document.getElementById('pdfUploadModal');
        pdfUploadModal.classList.toggle('show');
    }
    
    // Fonction pour échapper les caractères HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Fonction pour formater le message (liens, etc.)
    function formatMessage(text) {
        // Convertir les URLs en liens cliquables
        return text.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" class="text-info">$1</a>'
        );
    }
});