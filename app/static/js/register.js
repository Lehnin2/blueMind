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
    
    // Form validation
    const registerForm = document.getElementById('register-form');
    const registerError = document.getElementById('register-error');
    const confirmPassword = document.getElementById('confirm-password');
    
    if (registerForm && registerError && confirmPassword && password) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Check if passwords match
            if (password.value !== confirmPassword.value) {
                registerError.textContent = 'Les mots de passe ne correspondent pas.';
                registerError.style.display = 'block';
                return;
            }
            
            // Prepare form data - remove confirm_password and terms as they're not expected by the API
            const formData = new FormData(registerForm);
            
            // Keep terms for validation but don't send it to the API
            if (!formData.get('terms')) {
                registerError.textContent = 'Vous devez accepter les conditions d\'utilisation.';
                registerError.style.display = 'block';
                return;
            }
            
            // Create JSON object with only the required fields
            const userData = {
                name: formData.get('name'),
                email: formData.get('email'),
                password: formData.get('password')
            };
            
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
            
            // Accepter n'importe quel compte sans vérification
            // Simuler une inscription réussie
            console.log('Inscription réussie:', userData);
            
            // Afficher une notification de succès
            showNotification(`Inscription réussie! Bienvenue ${userData.name}`, 'success');
            
            // Rediriger vers la page de connexion après un court délai
            setTimeout(() => {
                window.location.href = '/login?registered=true';
            }, 1500);
        });
    }
});