let notificationPollingInterval;
let lastNotificationContent = '';

// Show a toast notification
function showNotification(message, type = 'info') {
    const toastElement = document.getElementById('notification-toast');
    const toastContent = document.getElementById('notification-content');
    
    if (toastElement && toastContent) {
        // Remove previous toast classes
        toastElement.classList.remove('info', 'success', 'error');
        // Add the type class
        toastElement.classList.add(type);
        
        // Add floating animation class
        toastElement.classList.add('floating-notification');
        
        // Set content
        toastContent.textContent = message;
        
        // Create Bootstrap toast instance and show it
        const toast = new bootstrap.Toast(toastElement, {
            autohide: type === 'success' || type === 'error',
            delay: 10000
        });
        toast.show();
        
        // Remove floating animation after delay
        setTimeout(() => {
            toastElement.classList.remove('floating-notification');
        }, 5000);
    }
}

// Start polling for notification updates
function startNotificationPolling() {
    // Clear any existing polling interval
    if (notificationPollingInterval) {
        clearInterval(notificationPollingInterval);
    }
    
    // Poll every 5 seconds
    notificationPollingInterval = setInterval(async function() {
        await checkNotification();
    }, 5000);
    
    // Initial check
    checkNotification();
}

// Check for notification updates
async function checkNotification() {
    try {
        const response = await fetch('/notification');
        const data = await response.json();
        
        // Only show notification if content has changed
        if (data.content && data.content !== lastNotificationContent) {
            lastNotificationContent = data.content;
            showNotification(data.content, data.type);
            
            // If notification is final (success or error), stop polling and update UI
            if (data.type === 'success') {
                stopNotificationPolling();
                const tasks = data.tasks || ['weather', 'fishing', 'diving', 'safety'];
                updateUI(tasks);
            } else if (data.type === 'error') {
                stopNotificationPolling();
            }
        }
    } catch (error) {
        console.error('Error checking notification:', error);
    }
}

// Stop polling for notification updates
function stopNotificationPolling() {
    if (notificationPollingInterval) {
        clearInterval(notificationPollingInterval);
        notificationPollingInterval = null;
    }
}