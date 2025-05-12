document.addEventListener('DOMContentLoaded', function() {
    // Toggle password visibility
    const togglePassword = document.getElementById('toggle-password');
    const password = document.getElementById('password');
    
    if (togglePassword && password) {
        togglePassword.addEventListener('click', function() {
            const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
            password.setAttribute('type', type);
            this.querySelector('i').classList.toggle('bi-eye');
            this.querySelector('i').classList.toggle('bi-eye-slash');
        });
    }
    
    // Créer une notification
    function showNotification(message, type = 'success') {
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
        
        // Supprimer automatiquement après 5 secondes
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
    
    // Form submission
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');
    
    if (loginForm && loginError) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            // Créer les données du formulaire
            const formData = new FormData();
            formData.append('email', email);
            formData.append('password', password);
            
            // Envoyer la requête au serveur
            fetch('/api/auth/login', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur d\'authentification');
                }
                return response.json();
            })
            .then(data => {
                // Afficher une notification de succès
                showNotification(`Connexion réussie! Bienvenue ${email}`, 'success');
                
                // Rediriger vers la page d'accueil après un court délai
                setTimeout(() => {
                    window.location.href = '/?logged_in=true';
                }, 1500);
            })
            .catch(error => {
                // Afficher l'erreur
                loginError.style.display = 'block';
                console.error('Erreur:', error);
            });
        });
    }
    
    // Vérifier si l'utilisateur vient de s'inscrire
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('registered') === 'true') {
        showNotification('Inscription réussie! Vous pouvez maintenant vous connecter.', 'info');
    }
});