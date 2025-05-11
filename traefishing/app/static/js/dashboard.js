// Update the current time
function updateTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        timeElement.textContent = `${hours}:${minutes}:${seconds}`;
    }
}

// Update compass direction randomly (for demo purposes)
function updateCompass() {
    const compassArrow = document.querySelector('.compass-arrow');
    if (compassArrow) {
        // In a real app, this would use actual heading data
        const randomDegree = Math.floor(Math.random() * 10) - 5; // Small random change
        const currentRotation = getComputedStyle(compassArrow).transform;
        let currentDegree = 45; // Default rotation
        
        if (currentRotation !== 'none') {
            // Extract current rotation if it exists
            const values = currentRotation.split('(')[1].split(')')[0].split(',');
            const a = values[0];
            const b = values[1];
            currentDegree = Math.round(Math.atan2(b, a) * (180/Math.PI));
        }
        
        const newDegree = currentDegree + randomDegree;
        compassArrow.style.transform = `rotate(${newDegree}deg)`;
    }
}

// Add random blips to radar (for demo purposes)
function updateRadarBlips() {
    const radar = document.querySelector('.radar');
    if (radar) {
        // Remove old blips
        const oldBlips = document.querySelectorAll('.radar-blip');
        oldBlips.forEach(blip => {
            // 20% chance to remove a blip
            if (Math.random() < 0.2) {
                blip.remove();
            }
        });
        
        // Add new blips occasionally
        if (Math.random() < 0.3 && oldBlips.length < 5) {
            const blip = document.createElement('div');
            blip.className = 'radar-blip';
            
            // Random position within the radar circle
            const angle = Math.random() * 2 * Math.PI;
            const radius = Math.random() * 45 + 5; // Between 5% and 50% of radar radius
            const x = 50 + Math.cos(angle) * radius;
            const y = 50 + Math.sin(angle) * radius;
            
            blip.style.left = `${x}%`;
            blip.style.top = `${y}%`;
            
            radar.appendChild(blip);
        }
    }
}

// Initialize dashboard
function initDashboard() {
    // Set initial time
    updateTime();
    
    // Update time every second
    setInterval(updateTime, 1000);
    
    // Update compass every 3 seconds
    setInterval(updateCompass, 3000);
    
    // Update radar blips every 2 seconds
    setInterval(updateRadarBlips, 2000);
}

// Run initialization when DOM is loaded
document.addEventListener('DOMContentLoaded', initDashboard);