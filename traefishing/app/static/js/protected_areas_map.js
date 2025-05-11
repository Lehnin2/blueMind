// Script pour gérer les interactions avec la carte dans protected_areas.html

document.addEventListener('DOMContentLoaded', function() {
    // Attendre que la carte Leaflet soit complètement chargée
    setTimeout(() => {
        initMapClickHandler();
    }, 500);

    function initMapClickHandler() {
        // Récupérer la carte Leaflet qui a été injectée par le backend
        const mapContainer = document.querySelector('.map-container');
        if (!mapContainer) return;

        // Récupérer l'instance de carte Leaflet
        // La carte est générée par folium et injectée dans le HTML
        const leafletMap = findLeafletMap();
        if (!leafletMap) {
            console.warn('Carte Leaflet non trouvée');
            return;
        }

        console.log('Carte Leaflet trouvée, ajout du gestionnaire de clic');

        // Récupérer les champs de saisie de latitude et longitude
        const latInput = document.getElementById('search_lat');
        const lonInput = document.getElementById('search_lon');

        // Ajouter un gestionnaire d'événement pour les clics sur la carte
        leafletMap.on('click', function(e) {
            const lat = e.latlng.lat;
            const lon = e.latlng.lng;
            
            // Mettre à jour les champs de saisie avec les coordonnées du clic
            latInput.value = lat.toFixed(4);
            lonInput.value = lon.toFixed(4);
            
            console.log(`Coordonnées sélectionnées: ${lat.toFixed(4)}, ${lon.toFixed(4)}`);
        });
    }

    // Fonction pour trouver l'instance de carte Leaflet dans le DOM
    function findLeafletMap() {
        // Rechercher l'objet map dans le contexte global (window)
        if (window.map && typeof window.map.on === 'function') {
            return window.map;
        }

        // Si la carte n'est pas exposée globalement, chercher dans les éléments iframe
        const mapIframe = document.querySelector('.map-container iframe');
        if (mapIframe && mapIframe.contentWindow) {
            try {
                // Essayer d'accéder à l'objet map dans l'iframe
                const iframeMap = mapIframe.contentWindow.map;
                if (iframeMap && typeof iframeMap.on === 'function') {
                    return iframeMap;
                }
            } catch (e) {
                console.warn('Impossible d\'accéder à la carte dans l\'iframe:', e);
            }
        }

        // Dernière tentative: chercher tous les objets Leaflet dans le DOM
        const leafletObjects = document.querySelectorAll('.leaflet-container');
        for (const container of leafletObjects) {
            // Vérifier si l'élément a un objet _leaflet associé
            if (container._leaflet_id) {
                // Récupérer l'instance de carte à partir de l'ID Leaflet
                const mapInstance = L.map._instances ? L.map._instances[container._leaflet_id] : null;
                if (mapInstance) {
                    return mapInstance;
                }
            }
        }

        return null;
    }
});