document.addEventListener('DOMContentLoaded', function() {
    // Initialisation de la carte
    const map = L.map('map').setView([46.603354, 1.888334], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    let marker = null;

    // Gestionnaire d'événements pour le clic sur la carte
    map.on('click', function(e) {
        if (marker) {
            map.removeLayer(marker);
        }
        marker = L.marker(e.latlng).addTo(map);
        document.getElementById('city').value = `${e.latlng.lat},${e.latlng.lng}`;
    });

    // Gestionnaire de soumission du formulaire
    document.getElementById('weatherForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const city = document.getElementById('city').value;
        if (!city) {
            showError('Veuillez entrer une ville ou cliquer sur la carte');
            return;
        }

        // Requête pour la météo actuelle
        fetch('/api/weather/current', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `city=${encodeURIComponent(city)}`
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur lors de la récupération des données météo');
            }
            return response.json();
        })
        .then(data => {
            displayWeather(data);
            return fetch('/api/weather/forecast', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `city=${encodeURIComponent(city)}&days=5`
            });
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur lors de la récupération des prévisions');
            }
            return response.json();
        })
        .then(data => {
            displayForecast(data);
        })
        .catch(error => {
            showError(error.message);
        });
    });
});

function displayWeather(data) {
    const weatherDiv = document.getElementById('weather');
    const fishingDiv = document.getElementById('fishing');

    weatherDiv.innerHTML = `
        <h2>Météo actuelle à ${data.location}</h2>
        <p>Température: ${data.temperature}°C</p>
        <p>Conditions: ${data.conditions}</p>
        <p>Humidité: ${data.humidity}%</p>
        <p>Vitesse du vent: ${data.wind_speed} km/h</p>
    `;

    fishingDiv.innerHTML = `
        <h2>Conditions de pêche</h2>
        <p>${data.fishing_conditions}</p>
    `;
}

function displayForecast(data) {
    const forecastDiv = document.getElementById('forecast');
    forecastDiv.innerHTML = '<h2>Prévisions sur 5 jours</h2>';

    data.forecast.forEach(day => {
        forecastDiv.innerHTML += `
            <div class="forecast-day">
                <h3>${day.date}</h3>
                <p>Température: ${day.temperature}°C</p>
                <p>Conditions: ${day.conditions}</p>
                <p>Humidité: ${day.humidity}%</p>
                <p>Vitesse du vent: ${day.wind_speed} km/h</p>
            </div>
        `;
    });
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
} 