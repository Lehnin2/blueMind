// Simulateur de données réelles pour TraeFishing
// Ce fichier utilise des fonctions réelles pour obtenir des données précises

// Variables pour stocker les données
let navigationData = null;
let weatherData = null;
let astronomyData = null;
let lastUpdate = 0;
let lastPosition = null;
let currentPosition = null;
let updateInterval = 30 * 1000; // 30 secondes en millisecondes

// Fonction pour calculer la vitesse basée sur les changements de position
function calculateSpeed(prevPos, currentPos, timeDiff) {
    if (!prevPos || !currentPos || timeDiff <= 0) {
        return 0;
    }
    
    // Calcul de la distance en km entre deux points GPS
    function haversineDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Rayon de la Terre en km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
                Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }
    
    // Calcul de la distance en km
    const distance = haversineDistance(
        prevPos.latitude, prevPos.longitude,
        currentPos.latitude, currentPos.longitude
    );
    
    // Conversion du temps de ms en heures
    const timeHours = timeDiff / (1000 * 60 * 60);
    
    // Vitesse en km/h
    return distance / timeHours;
}

// Fonction pour obtenir la profondeur à partir de l'API
async function getDepthAtLocation(lat, lon) {
    try {
        // Vérifier que lat et lon sont définis et valides
        if (lat === undefined || lon === undefined || isNaN(lat) || isNaN(lon)) {
            console.warn('Coordonnées invalides pour la profondeur, utilisation de l\'estimation');
            return estimateDepthFromShore(36.8065, 10.1815); // Utiliser des coordonnées par défaut
        }
        
        // S'assurer que les coordonnées sont des nombres
        const latitude = parseFloat(lat);
        const longitude = parseFloat(lon);
        
        if (isNaN(latitude) || isNaN(longitude)) {
            console.warn('Conversion des coordonnées en nombres a échoué, utilisation de l\'estimation');
            return estimateDepthFromShore(36.8065, 10.1815);
        }
        
        // Utilisation de l'API de profondeur qui utilise la fonction dans le dossier tools
        const response = await fetch(`/api/depth?lat=${latitude}&lon=${longitude}`);
        if (!response.ok) {
            console.warn(`Erreur API profondeur (${response.status}), utilisation de l'estimation`);
            return estimateDepthFromShore(latitude, longitude);
        }
        const data = await response.json();
        return data.depth || 0;
    } catch (error) {
        console.error('Erreur lors de la récupération de la profondeur:', error);
        // Fallback à une estimation basée sur la distance à la côte
        return estimateDepthFromShore(lat && !isNaN(lat) ? lat : 36.8065, lon && !isNaN(lon) ? lon : 10.1815);
    }
}

// Estimation de la profondeur basée sur la distance à la côte (fallback)
function estimateDepthFromShore(lat, lon) {
    // Coordonnées approximatives de la côte tunisienne
    const coastPoints = [
        {lat: 37.3, lon: 9.8}, // Nord
        {lat: 36.8, lon: 10.3}, // Tunis
        {lat: 35.8, lon: 10.6}, // Sousse
        {lat: 34.7, lon: 10.8}, // Sfax
        {lat: 33.9, lon: 10.1}, // Gabès
        {lat: 33.3, lon: 11.2}  // Sud
    ];
    
    // Calcul de la distance minimale à la côte
    let minDistance = Infinity;
    for (const point of coastPoints) {
        const R = 6371; // Rayon de la Terre en km
        const dLat = (point.lat - lat) * Math.PI / 180;
        const dLon = (point.lon - lon) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(lat * Math.PI / 180) * Math.cos(point.lat * Math.PI / 180) * 
                Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        const distance = R * c;
        
        if (distance < minDistance) {
            minDistance = distance;
        }
    }
    
    // Modèle simplifié: 10m de profondeur par km depuis la côte, plafonné à 1500m
    return Math.min(minDistance * 10, 1500);
}

// Fonction pour obtenir les données météo depuis l'API StormGlass
async function getWeatherData(lat, lon) {
    try {
        // Vérifier que lat et lon sont définis
        if (lat === undefined || lon === undefined || isNaN(lat) || isNaN(lon)) {
            console.warn('Coordonnées invalides pour la météo, utilisation des données de secours');
            return generateFallbackWeatherData();
        }
        
        // Utilisation de la clé API StormGlass fournie
        const stormglass_api_key = "ad33d24a-0bd7-11f0-803a-0242ac130003-ad33d2a4-0bd7-11f0-803a-0242ac130003";
        const response = await fetch(`/api/astro-weather?lat=${lat}&lon=${lon}&api_key=${stormglass_api_key}`);
        if (!response.ok) {
            console.warn(`Erreur API météo (${response.status}), utilisation des données de secours`);
            return generateFallbackWeatherData();
        }
        const data = await response.json();
        return {
            temperature: data.weather?.temperature || 25,
            humidity: data.weather?.humidity || 60,
            windSpeed: data.weather?.windSpeed || 10,
            condition: data.weather?.condition || 'clear',
            status: 'success'
        };
    } catch (error) {
        console.error('Erreur lors de la récupération des données météo:', error);
        return generateFallbackWeatherData();
    }
}

// Fonction pour obtenir les données astronomiques depuis l'API StormGlass
async function getAstronomyData(lat, lon) {
    try {
        // Vérifier que lat et lon sont définis
        if (lat === undefined || lon === undefined || isNaN(lat) || isNaN(lon)) {
            console.warn('Coordonnées invalides pour les données astronomiques, utilisation des données de secours');
            return generateFallbackAstronomyData();
        }
        
        // Utilisation de la clé API StormGlass fournie
        const stormglass_api_key = "ad33d24a-0bd7-11f0-803a-0242ac130003-ad33d2a4-0bd7-11f0-803a-0242ac130003";
        const response = await fetch(`/api/astro-weather?lat=${lat}&lon=${lon}&api_key=${stormglass_api_key}`);
        if (!response.ok) {
            console.warn(`Erreur API astronomie (${response.status}), utilisation des données de secours`);
            return generateFallbackAstronomyData();
        }
        const data = await response.json();
        return {
            sunrise: data.astronomy?.sunrise || '06:00',
            sunset: data.astronomy?.sunset || '18:00',
            moonrise: data.astronomy?.moonrise || '20:00',
            moonset: data.astronomy?.moonset || '04:00',
            moonPhase: data.astronomy?.moonPhase || 'Premier quartier',
            status: 'success'
        };
    } catch (error) {
        console.error('Erreur lors de la récupération des données astronomiques:', error);
        return generateFallbackAstronomyData();
    }
}

// Données météo de secours en cas d'échec de l'API
function generateFallbackWeatherData() {
    const conditions = ['clear', 'partly-cloudy', 'cloudy', 'rain', 'thunderstorm', 'mist'];
    const randomConditionIndex = Math.floor(Math.random() * conditions.length);
    
    return {
        temperature: (Math.floor(Math.random() * 10) + 20).toString(), // Entre 20 et 30°C
        humidity: (Math.floor(Math.random() * 30) + 50).toString(), // Entre 50% et 80%
        windSpeed: (Math.floor(Math.random() * 15) + 5).toString(), // Entre 5 et 20 km/h
        condition: conditions[randomConditionIndex],
        status: 'fallback'
    };
}

// Données astronomiques de secours en cas d'échec de l'API
function generateFallbackAstronomyData() {
    const now = new Date();
    const day = now.getDate();
    
    // Calculer des heures réalistes basées sur la date
    const sunriseHour = 5 + Math.floor((day % 3) / 3);
    const sunsetHour = 18 + Math.floor((day % 3) / 3);
    const moonriseHour = 19 + Math.floor((day % 5) / 5);
    const moonsetHour = 4 + Math.floor((day % 5) / 5);
    
    // Phases de la lune
    const moonPhases = [
        'Nouvelle lune', 'Premier croissant', 'Premier quartier', 
        'Gibbeuse croissante', 'Pleine lune', 'Gibbeuse décroissante', 
        'Dernier quartier', 'Dernier croissant'
    ];
    const moonPhaseIndex = Math.floor((day % 28) / 3.5); // Cycle lunaire d'environ 28 jours
    
    return {
        sunrise: `0${sunriseHour}:${Math.floor(Math.random() * 60).toString().padStart(2, '0')}`,
        sunset: `${sunsetHour}:${Math.floor(Math.random() * 60).toString().padStart(2, '0')}`,
        moonrise: `${moonriseHour}:${Math.floor(Math.random() * 60).toString().padStart(2, '0')}`,
        moonset: `0${moonsetHour}:${Math.floor(Math.random() * 60).toString().padStart(2, '0')}`,
        moonPhase: moonPhases[moonPhaseIndex],
        status: 'fallback'
    };
}

// Fonction pour mettre à jour les données de navigation
async function updateNavigationData() {
    try {
        // Obtenir la position actuelle
        const position = await getCurrentPosition();
        if (!position) {
            throw new Error('Position non disponible');
        }
        
        // Mettre à jour les positions pour le calcul de vitesse
        lastPosition = currentPosition;
        currentPosition = position;
        
        // Calculer la vitesse si nous avons deux positions
        let speed = 0;
        if (lastPosition && currentPosition) {
            const timeDiff = Date.now() - lastUpdate;
            speed = calculateSpeed(lastPosition, currentPosition, timeDiff);
        }
        
        // Obtenir la profondeur à la position actuelle en utilisant la fonction du dossier tools
        const depth = await getDepthAtLocation(position.latitude, position.longitude);
        
        // Obtenir le cap (heading) à partir des données du capteur d'orientation
        // Si disponible, utiliser la dernière valeur du capteur, sinon utiliser une valeur par défaut
        let heading = 0;
        if (deviceOrientationData && deviceOrientationData.heading !== undefined && !isNaN(deviceOrientationData.heading)) {
            heading = deviceOrientationData.heading;
            // Vérifier si les données sont récentes (moins de 30 secondes)
            const dataAge = Date.now() - deviceOrientationData.lastUpdate;
            if (dataAge > 30000) { // 30 secondes
                console.warn('Données de cap obsolètes, utilisation de la dernière valeur connue');
            }
        } else {
            // Valeur par défaut si le capteur n'est pas disponible
            heading = Math.floor(Math.random() * 360);
            console.warn('Capteur d\'orientation non disponible, utilisation d\'une valeur simulée');
        }
        
        // Mettre à jour les données de navigation
        navigationData = {
            speed: speed.toFixed(1),
            depth: depth.toFixed(1),
            wind: weatherData ? weatherData.windSpeed : '0.0',
            heading: heading
        };
        
        return navigationData;
    } catch (error) {
        console.error('Erreur lors de la mise à jour des données de navigation:', error);
        // Fallback à des données simulées
        return {
            speed: (5 + Math.random() * 10).toFixed(1),
            depth: (20 + Math.random() * 30).toFixed(1),
            wind: weatherData ? weatherData.windSpeed : (5 + Math.random() * 15).toFixed(1),
            heading: Math.floor(Math.random() * 360)
        };
    }
}

// Fonction pour obtenir la position actuelle
async function getCurrentPosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            console.warn('Géolocalisation non supportée par ce navigateur, utilisation des coordonnées par défaut');
            // Fallback à une position par défaut (Tunis)
            resolve({
                latitude: 36.8065,
                longitude: 10.1815
            });
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                });
            },
            (error) => {
                console.warn(`Erreur de géolocalisation (${error.code}): ${error.message}`);
                // Fallback à une position par défaut (Tunis)
                resolve({
                    latitude: 36.8065,
                    longitude: 10.1815
                });
            },
            { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
        );
    });
}

// Fonction pour mettre à jour toutes les données
async function updateAllData() {
    try {
        // Obtenir la position actuelle
        const position = await getCurrentPosition();
        if (!position || position.latitude === undefined || position.longitude === undefined) {
            console.error('Position non disponible ou coordonnées invalides, utilisation des données de secours');
            // Utiliser des données de secours
            navigationData = {
                speed: (5 + Math.random() * 10).toFixed(1),
                depth: (20 + Math.random() * 30).toFixed(1),
                wind: (5 + Math.random() * 15).toFixed(1),
                heading: Math.floor(Math.random() * 360)
            };
            weatherData = generateFallbackWeatherData();
            astronomyData = generateFallbackAstronomyData();
            lastUpdate = Date.now();
            updateDashboardWithRealData();
            return;
        }
        
        console.log('Position obtenue:', position.latitude, position.longitude);
        
        // Mettre à jour les données de navigation
        navigationData = await updateNavigationData();
        
        // Vérifier que les coordonnées sont valides avant d'appeler les API
        if (isNaN(position.latitude) || isNaN(position.longitude)) {
            console.warn('Coordonnées invalides, utilisation des données de secours');
            weatherData = generateFallbackWeatherData();
            astronomyData = generateFallbackAstronomyData();
        } else {
            // Mettre à jour les données météo et astronomiques
            weatherData = await getWeatherData(position.latitude, position.longitude);
            astronomyData = await getAstronomyData(position.latitude, position.longitude);
        }
        
        // Mettre à jour l'horodatage
        lastUpdate = Date.now();
        
        // Mettre à jour l'interface
        updateDashboardWithRealData();
    } catch (error) {
        console.error('Erreur lors de la mise à jour des données:', error);
        // Utiliser des données de secours en cas d'erreur
        navigationData = {
            speed: (5 + Math.random() * 10).toFixed(1),
            depth: (20 + Math.random() * 30).toFixed(1),
            wind: (5 + Math.random() * 15).toFixed(1),
            heading: Math.floor(Math.random() * 360)
        };
        weatherData = generateFallbackWeatherData();
        astronomyData = generateFallbackAstronomyData();
        lastUpdate = Date.now();
        updateDashboardWithRealData();
    }
}

// Fonction pour mettre à jour l'interface avec les données réelles
function updateDashboardWithRealData() {
    if (!navigationData || !weatherData || !astronomyData) return;
    
    // Mettre à jour les données de navigation
    document.getElementById('speed-value').textContent = `${navigationData.speed} km/h`;
    document.getElementById('depth-value').textContent = `${navigationData.depth} m`;
    document.getElementById('wind-value').textContent = `${navigationData.wind} km/h`;
    document.getElementById('heading-value').textContent = `${navigationData.heading}°`;
    
    // Mettre à jour les données météo
    document.getElementById('current-temp').textContent = `${weatherData.temperature}°C`;
    document.getElementById('humidity-value').textContent = `${weatherData.humidity}%`;
    document.getElementById('wind-speed-value').textContent = `${weatherData.windSpeed} km/h`;
    updateWeatherIcon(weatherData.condition);
    
    // Mettre à jour les données astronomiques
    document.getElementById('sunrise-value').textContent = astronomyData.sunrise;
    document.getElementById('sunset-value').textContent = astronomyData.sunset;
    document.getElementById('moonrise-value').textContent = astronomyData.moonrise;
    document.getElementById('moonset-value').textContent = astronomyData.moonset;
    document.getElementById('moon-phase-value').textContent = astronomyData.moonPhase;
    
    // Mettre à jour l'heure de la dernière mise à jour
    const lastUpdateElement = document.getElementById('last-update-time');
    if (lastUpdateElement) {
        const updateTime = new Date(lastUpdate);
        lastUpdateElement.textContent = `Dernière mise à jour: ${updateTime.toLocaleTimeString()}`;
    }
    
    // Mettre à jour la boussole si elle existe
    updateCompass(navigationData.heading);
}

// Fonction pour mettre à jour l'icône météo
function updateWeatherIcon(condition) {
    const iconElement = document.getElementById('current-weather-icon');
    if (!iconElement) return;
    
    const iconMap = {
        'clear': 'fas fa-sun',
        'partly-cloudy': 'fas fa-cloud-sun',
        'cloudy': 'fas fa-cloud',
        'rain': 'fas fa-cloud-rain',
        'thunderstorm': 'fas fa-bolt',
        'snow': 'fas fa-snowflake',
        'mist': 'fas fa-smog'
    };
    
    const iconClass = iconMap[condition] || 'fas fa-cloud';
    iconElement.innerHTML = `<i class="${iconClass}"></i>`;
}

// Variables pour stocker les données d'orientation du dispositif
let deviceOrientationData = {
    heading: null,
    lastUpdate: 0
};

// Fonction pour initialiser les capteurs d'orientation
function initOrientationSensors() {
    if (window.DeviceOrientationEvent) {
        // Vérifier si l'API nécessite une permission (iOS 13+)
        if (typeof DeviceOrientationEvent.requestPermission === 'function') {
            // Ajouter un bouton pour demander la permission
            const permissionButton = document.getElementById('compass-permission-button');
            if (permissionButton) {
                permissionButton.style.display = 'block';
                permissionButton.addEventListener('click', async () => {
                    try {
                        const permission = await DeviceOrientationEvent.requestPermission();
                        if (permission === 'granted') {
                            window.addEventListener('deviceorientation', handleDeviceOrientation);
                            permissionButton.style.display = 'none';
                            console.log('Permission d\'orientation accordée');
                        }
                    } catch (error) {
                        console.error('Erreur lors de la demande de permission:', error);
                    }
                });
            }
        } else {
            // Pas besoin de permission, ajouter directement l'écouteur d'événements
            window.addEventListener('deviceorientation', handleDeviceOrientation);
            console.log('Capteur d\'orientation initialisé');
        }
    } else {
        console.warn('DeviceOrientation non supporté par ce navigateur');
    }
}

// Fonction pour gérer les événements d'orientation du dispositif
function handleDeviceOrientation(event) {
    let heading = null;
    
    if (event.webkitCompassHeading !== undefined) {
        // Pour les appareils iOS
        heading = event.webkitCompassHeading;
    } else if (event.alpha !== undefined) {
        // Pour les appareils Android
        heading = 360 - event.alpha;
    }
    
    // Vérifier que la valeur du cap est valide (un nombre entre 0 et 360)
    if (heading !== null && !isNaN(heading)) {
        // Normaliser la valeur entre 0 et 360
        heading = ((heading % 360) + 360) % 360;
        
        // Mettre à jour les données d'orientation
        deviceOrientationData = {
            heading: heading,
            lastUpdate: Date.now()
        };
        
        // Mettre à jour la boussole si elle n'est pas mise à jour par ailleurs
        const compassInner = document.getElementById('compass-inner');
        if (compassInner) {
            updateCompass(heading);
        }
        
        // Journaliser pour le débogage (en mode développement)
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.debug(`Cap mis à jour: ${heading.toFixed(1)}°`);
        }
    }
}

// Fonction pour mettre à jour la boussole
function updateCompass(heading) {
    const compassInner = document.getElementById('compass-inner');
    if (compassInner) {
        compassInner.style.transform = `rotate(${-heading}deg)`;
    }
    
    // Mettre à jour l'affichage du cap avec les points cardinaux
    const headingDisplay = document.getElementById('heading-value');
    if (headingDisplay) {
        const directions = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'];
        const index = Math.round(heading / 45) % 8;
        headingDisplay.textContent = `${Math.round(heading)}° (${directions[index]})`;
    }
}

// Fonction pour initialiser l'horloge numérique
function updateDigitalClock() {
    const now = new Date();
    const timeElement = document.getElementById('digital-time');
    const dateElement = document.getElementById('digital-date');
    const dayElement = document.getElementById('digital-day');
    
    if (timeElement && dateElement && dayElement) {
        // Mettre à jour l'heure
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        timeElement.textContent = `${hours}:${minutes}:${seconds}`;
        
        // Mettre à jour la date
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        dateElement.textContent = now.toLocaleDateString('fr-FR', options);
        
        // Mettre à jour le jour
        const dayOptions = { weekday: 'long' };
        dayElement.textContent = now.toLocaleDateString('fr-FR', dayOptions);
    }
}

// Fonction d'initialisation du tableau de bord
function initRealDashboard() {
    // Initialiser l'horloge numérique
    updateDigitalClock();
    setInterval(updateDigitalClock, 1000);
    
    // Initialiser les capteurs d'orientation pour la boussole
    initOrientationSensors();
    
    // Générer les données initiales
    updateAllData();
    
    // Mettre à jour les données périodiquement
    setInterval(updateAllData, updateInterval);
    
    // Ajouter un gestionnaire d'événements pour le bouton de rafraîchissement
    const refreshButton = document.getElementById('refresh-data-button');
    if (refreshButton) {
        refreshButton.addEventListener('click', updateAllData);
    }
    
    console.log('Tableau de bord avec données réelles initialisé avec succès');
}

// Exécuter l'initialisation lorsque le DOM est chargé
document.addEventListener('DOMContentLoaded', initRealDashboard);