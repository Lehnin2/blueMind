// Variables pour stocker les données et l'état de rafraîchissement
let lastAstroWeatherUpdate = 0;
let astroWeatherData = null;
let updateInterval = 30 * 60 * 1000; // 30 minutes en millisecondes

// Fonction pour récupérer les données d'astronomie et météo via AJAX
async function fetchAstroWeatherData(lat, lon) {
    try {
        // Créer l'URL avec les paramètres de localisation du client
        const url = `/api/astro-weather?lat=${lat}&lon=${lon}`;
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        astroWeatherData = data;
        lastAstroWeatherUpdate = Date.now();
        
        // Mettre à jour l'interface avec les nouvelles données
        updateDashboardData(data);
        
        console.log('Données astro-météo mises à jour avec succès');
    } catch (error) {
        console.error('Erreur lors de la récupération des données:', error);
    }
}

// Update dashboard with received data
function updateDashboardData(data) {
    // Update navigation data
    if (data.navigation) {
        document.getElementById('speed-value').textContent = `${data.navigation.speed} km/h`;
        document.getElementById('depth-value').textContent = `${data.navigation.depth} m`;
        document.getElementById('wind-value').textContent = `${data.navigation.wind} km/h`;
        document.getElementById('heading-value').textContent = `${data.navigation.heading}°`;
    }
    
    // Update weather data
    if (data.weather) {
        document.getElementById('current-temp').textContent = `${data.weather.temperature}°C`;
        document.getElementById('humidity-value').textContent = `${data.weather.humidity}%`;
        document.getElementById('wind-speed-value').textContent = `${data.weather.windSpeed} km/h`;
        updateWeatherIcon(data.weather.condition);
    }
    
    // Update astronomy data
    if (data.astronomy) {
        document.getElementById('sunrise-value').textContent = data.astronomy.sunrise;
        document.getElementById('sunset-value').textContent = data.astronomy.sunset;
        document.getElementById('moonrise-value').textContent = data.astronomy.moonrise;
        document.getElementById('moonset-value').textContent = data.astronomy.moonset;
        document.getElementById('moon-phase-value').textContent = data.astronomy.moonPhase;
        
        // Ajouter l'heure de la dernière mise à jour
        const lastUpdateElement = document.getElementById('last-update-time');
        if (lastUpdateElement) {
            const updateTime = new Date(lastAstroWeatherUpdate);
            lastUpdateElement.textContent = `Dernière mise à jour: ${updateTime.toLocaleTimeString()}`;
        }
    }
}

// Vérifier si les données doivent être mises à jour
function checkForDataUpdate(lat, lon) {
    const now = Date.now();
    // Si les données n'ont jamais été chargées ou si l'intervalle de mise à jour est dépassé
    if (!astroWeatherData || (now - lastAstroWeatherUpdate) > updateInterval) {
        fetchAstroWeatherData(lat, lon);
    }
}

// Fonction pour rafraîchir manuellement les données
function refreshData() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            fetchAstroWeatherData(lat, lon);
        }, function(error) {
            console.error('Erreur de géolocalisation:', error);
            // Utiliser des coordonnées par défaut ou les dernières connues
            fetchAstroWeatherData(0, 0); // Coordonnées par défaut
        });
    } else {
        console.error('Géolocalisation non supportée');
        fetchAstroWeatherData(0, 0); // Coordonnées par défaut
    }
}

// Update weather icon based on condition
function updateWeatherIcon(condition) {
    const iconElement = document.getElementById('current-weather-icon');
    const iconClass = getWeatherIconClass(condition);
    iconElement.innerHTML = `<i class="${iconClass}"></i>`;
}

// Get weather icon class based on condition
function getWeatherIconClass(condition) {
    const iconMap = {
        'clear': 'fas fa-sun',
        'partly-cloudy': 'fas fa-cloud-sun',
        'cloudy': 'fas fa-cloud',
        'rain': 'fas fa-cloud-rain',
        'thunderstorm': 'fas fa-bolt',
        'snow': 'fas fa-snowflake',
        'mist': 'fas fa-smog'
    };
    return iconMap[condition] || 'fas fa-cloud';
}

// Initialize digital clock
function updateDigitalClock() {
    const now = new Date();
    const timeElement = document.getElementById('digital-time');
    const dateElement = document.getElementById('digital-date');
    const dayElement = document.getElementById('digital-day');
    
    if (timeElement && dateElement && dayElement) {
        // Update time
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        timeElement.textContent = `${hours}:${minutes}:${seconds}`;
        
        // Update date
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        dateElement.textContent = now.toLocaleDateString('fr-FR', options);
        
        // Update day
        const dayOptions = { weekday: 'long' };
        dayElement.textContent = now.toLocaleDateString('fr-FR', dayOptions);
    }
}

// Initialize dashboard
function initDashboard() {
    // Initialize digital clock
    updateDigitalClock();
    setInterval(updateDigitalClock, 1000);

    // Initialiser avec des données fictives en attendant les vraies données
    const mockData = {
        navigation: {
            speed: '0.0',
            depth: '0.0',
            wind: '0.0',
            heading: '0'
        },
        weather: {
            temperature: '25',
            humidity: '60',
            windSpeed: '10',
            condition: 'clear'
        },
        astronomy: {
            sunrise: '--:--',
            sunset: '--:--',
            moonrise: '--:--',
            moonset: '--:--',
            moonPhase: '--'
        }
    };
    updateDashboardData(mockData);
    
    // Récupérer la géolocalisation du client pour les données d'astronomie et météo
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            
            // Charger les données initiales
            fetchAstroWeatherData(lat, lon);
            
            // Vérifier périodiquement si les données doivent être mises à jour
            // mais sans forcer une mise à jour constante
            setInterval(() => checkForDataUpdate(lat, lon), 5 * 60 * 1000); // Vérifier toutes les 5 minutes
        }, function(error) {
            console.error('Erreur de géolocalisation:', error);
            // Utiliser des coordonnées par défaut
            fetchAstroWeatherData(0, 0);
        });
    } else {
        console.error('Géolocalisation non supportée');
        // Utiliser des coordonnées par défaut
        fetchAstroWeatherData(0, 0);
    }
    
    // Ajouter un bouton de rafraîchissement manuel
    const refreshButton = document.getElementById('refresh-data-button');
    if (refreshButton) {
        refreshButton.addEventListener('click', refreshData);
    }
}

// Run initialization when DOM is loaded
document.addEventListener('DOMContentLoaded', initDashboard);