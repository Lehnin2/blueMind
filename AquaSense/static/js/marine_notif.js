document.addEventListener('DOMContentLoaded', function() {
    const maritimeForm = document.getElementById('maritime-form');
    const loadingSpinner = document.getElementById('loading-spinner');
    const submitBtn = document.getElementById('submit-btn');
    const resultsSection = document.getElementById('results-section');
    
    let notificationPollingInterval;
    let lastNotificationContent = '';

    if (maritimeForm) {
        maritimeForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            loadingSpinner.classList.remove('d-none');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
            showNotification('Processing maritime data... This may take a few minutes.', 'info');
            const formData = new FormData(maritimeForm);
            try {
                const response = await fetch('/run_maritime_watch', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (data.status === 'success') {
                    startNotificationPolling();
                } else {
                    showNotification('Error: ' + data.message, 'error');
                    resetForm();
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification('An error occurred while processing your request.', 'error');
                resetForm();
            }
        });
    }
    
    function resetForm() {
        loadingSpinner.classList.add('d-none');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Get Maritime Information';
    }
    
    async function fetchResearchContent(taskType) {
        try {
            const response = await fetch(`/research/${taskType}`);
            const data = await response.json();
            if (response.ok) {
                const contentElement = document.getElementById(`${taskType}-content`);
                const accordionElement = document.getElementById(`${taskType}-accordion`);
                if (contentElement && accordionElement) {
                    contentElement.innerHTML = marked.parse(data.content);
                    accordionElement.style.display = 'block';
                }
            } else {
                console.error(`Error fetching ${taskType} content:`, data.error);
            }
        } catch (error) {
            console.error(`Error fetching ${taskType} content:`, error);
        }
    }
    
    async function fetchSummary() {
        try {
            const response = await fetch('/summary');
            const data = await response.json();
            if (response.ok) {
                const summaryElement = document.getElementById('summary-content');
                if (summaryElement) {
                    summaryElement.textContent = data.content;
                    resultsSection.style.display = 'block';
                }
            } else {
                console.error('Error fetching summary:', data.error);
            }
        } catch (error) {
            console.error('Error fetching summary:', error);
        }
    }
    
    window.updateUI = function(taskTypes) {
        resetForm();
        taskTypes.forEach(taskType => {
            fetchResearchContent(taskType);
        });
        fetchSummary();
    };
    
    function showNotification(message, type = 'info') {
        const toastElement = document.getElementById('notification-toast');
        const toastContent = document.getElementById('notification-content');
        if (toastElement && toastContent) {
            toastElement.classList.remove('info', 'success', 'error');
            toastElement.classList.add(type);
            toastElement.classList.add('floating-notification');
            toastContent.textContent = message;
            const toast = new bootstrap.Toast(toastElement, {
                autohide: type === 'success' || type === 'error',
                delay: 10000
            });
            toast.show();
            setTimeout(() => {
                toastElement.classList.remove('floating-notification');
            }, 5000);
        }
    }
    
    function startNotificationPolling() {
        if (notificationPollingInterval) {
            clearInterval(notificationPollingInterval);
        }
        notificationPollingInterval = setInterval(async function() {
            await checkNotification();
        }, 5000);
        checkNotification();
    }
    
    async function checkNotification() {
        try {
            const response = await fetch('/notification');
            const data = await response.json();
            if (data.content && data.content !== lastNotificationContent) {
                lastNotificationContent = data.content;
                showNotification(data.content, data.type);
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
    
    function stopNotificationPolling() {
        if (notificationPollingInterval) {
            clearInterval(notificationPollingInterval);
            notificationPollingInterval = null;
        }
    }
    
    const markdownElements = document.querySelectorAll('.markdown-content');
    markdownElements.forEach(element => {
        element.innerHTML = marked.parse(element.textContent);
    });
});