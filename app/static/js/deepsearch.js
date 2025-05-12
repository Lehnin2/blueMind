/**
 * Module de recherche web DeepSearch pour l'assistant intelligent
 * Ce script gère l'intégration de la recherche web via l'API xAI DeepSearch
 */

// Fonction pour effectuer une recherche web via l'API DeepSearch
async function performWebSearch(query, language = 'fr') {
    try {
        // Afficher un indicateur de chargement
        showLoadingIndicator();
        
        // Préparer les données pour la requête
        const formData = new FormData();
        formData.append('query', query);
        formData.append('language', language);
        
        // Envoyer la requête à l'API
        const response = await fetch('/api/web-search', {
            method: 'POST',
            body: formData
        });
        
        // Vérifier si la requête a réussi
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        // Analyser la réponse JSON
        const data = await response.json();
        
        // Masquer l'indicateur de chargement
        hideLoadingIndicator();
        
        return data;
    } catch (error) {
        // Masquer l'indicateur de chargement en cas d'erreur
        hideLoadingIndicator();
        
        console.error('Erreur lors de la recherche web:', error);
        return {
            response: "Erreur lors de la recherche web. Veuillez réessayer ultérieurement.",
            sources: [],
            suggestions: [],
            warning: error.message
        };
    }
}

// Fonction pour afficher l'indicateur de chargement
function showLoadingIndicator() {
    // Créer l'élément d'indicateur de chargement s'il n'existe pas déjà
    if (!document.getElementById('search-loading-indicator')) {
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'search-loading-indicator';
        loadingIndicator.className = 'typing-indicator';
        loadingIndicator.innerHTML = `
            <span>Recherche en cours</span>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        
        // Ajouter l'indicateur à la zone de messages du chat
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.appendChild(loadingIndicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
}

// Fonction pour masquer l'indicateur de chargement
function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('search-loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

// Fonction pour ajouter un message de recherche web au chat
function addWebSearchMessage(data) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    // Créer le conteneur du message
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    // Formater le contenu du message
    let messageContent = `<div class="message-content">${data.response}</div>`;
    
    // Ajouter les sources si disponibles
    if (data.sources && data.sources.length > 0) {
        messageContent += '<div class="message-sources"><strong>Sources:</strong><ul>';
        data.sources.forEach(source => {
            messageContent += `<li><a href="${source.url}" target="_blank">${source.title || source.url}</a></li>`;
        });
        messageContent += '</ul></div>';
    }
    
    // Ajouter l'horodatage
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    messageContent += `<div class="message-time">Aujourd'hui, ${timeString}</div>`;
    
    // Définir le contenu HTML du message
    messageDiv.innerHTML = messageContent;
    
    // Ajouter le message à la zone de chat
    chatMessages.appendChild(messageDiv);
    
    // Faire défiler vers le bas pour afficher le nouveau message
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Ajouter les suggestions si disponibles
    if (data.suggestions && data.suggestions.length > 0) {
        updateSuggestions(data.suggestions);
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
            // Insérer la suggestion dans la zone de texte
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                messageInput.value = suggestion;
                messageInput.focus();
            }
        });
        
        suggestionsContainer.appendChild(chip);
    });
}

// Fonction pour détecter si une requête nécessite une recherche web
function needsWebSearch(query) {
    // Liste de mots-clés qui pourraient indiquer le besoin d'une recherche web
    const webSearchKeywords = [
        'recherche', 'cherche', 'trouve', 'internet', 'web', 'en ligne',
        'actualité', 'récent', 'dernière', 'nouveau', 'nouvelle',
        'information', 'info', 'à jour', 'mise à jour',
        'search', 'find', 'look up', 'online'
    ];
    
    // Vérifier si la requête contient l'un des mots-clés
    const queryLower = query.toLowerCase();
    return webSearchKeywords.some(keyword => queryLower.includes(keyword.toLowerCase()));
}

// Exporter les fonctions pour les rendre disponibles globalement
window.DeepSearch = {
    performWebSearch,
    addWebSearchMessage,
    needsWebSearch
};