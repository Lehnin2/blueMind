/**
 * Système de notifications pour l'application
 * Ce fichier permet d'afficher des notifications à l'utilisateur
 */

const NotificationSystem = {
    /**
     * Affiche une notification à l'utilisateur
     * @param {string} message - Le message à afficher
     * @param {string} type - Le type de notification (success, info, warning, danger)
     * @param {number} duration - La durée d'affichage en millisecondes
     */
    show: function(message, type = 'success', duration = 5000) {
        // Créer l'élément de notification s'il n'existe pas déjà
        let notifContainer = document.getElementById('notification-container');
        if (!notifContainer) {
            notifContainer = document.createElement('div');
            notifContainer.id = 'notification-container';
            notifContainer.style.position = 'fixed';
            notifContainer.style.top = '20px';
            notifContainer.style.right = '20px';
            notifContainer.style.zIndex = '9999';
            document.body.appendChild(notifContainer);
        }
        
        // Créer la notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Ajouter la notification au conteneur
        notifContainer.appendChild(notification);
        
        // Supprimer automatiquement après la durée spécifiée
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    },

    /**
     * Affiche une notification de succès
     * @param {string} message - Le message à afficher
     */
    success: function(message, duration = 5000) {
        this.show(message, 'success', duration);
    },

    /**
     * Affiche une notification d'information
     * @param {string} message - Le message à afficher
     */
    info: function(message, duration = 5000) {
        this.show(message, 'info', duration);
    },

    /**
     * Affiche une notification d'avertissement
     * @param {string} message - Le message à afficher
     */
    warning: function(message, duration = 5000) {
        this.show(message, 'warning', duration);
    },

    /**
     * Affiche une notification d'erreur
     * @param {string} message - Le message à afficher
     */
    error: function(message, duration = 5000) {
        this.show(message, 'danger', duration);
    }
};

// Exposer le système de notifications globalement
window.NotificationSystem = NotificationSystem;

// Vérifier si l'utilisateur vient de s'inscrire ou de se connecter
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Notification après inscription
    if (urlParams.get('registered') === 'true') {
        NotificationSystem.success('Inscription réussie! Vous pouvez maintenant vous connecter.');
    }
    
    // Notification après connexion
    if (urlParams.get('logged_in') === 'true') {
        NotificationSystem.success('Connexion réussie! Bienvenue.');
    }
});