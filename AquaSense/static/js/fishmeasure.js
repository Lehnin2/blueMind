 let map;
        let marker;

        function initializeMap() {
            const mapContainer = document.getElementById('map');
            if (!mapContainer) return;

            map = L.map('map').setView([34.0, 9.0], 6);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap'
            }).addTo(map);

            map.on('click', function (e) {
                const { lat, lng } = e.latlng;
                document.getElementById('lat').value = lat;
                document.getElementById('lng').value = lng;

                if (marker) map.removeLayer(marker);
                marker = L.marker([lat, lng]).addTo(map);
            });

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const { latitude, longitude } = position.coords;
                        map.setView([latitude, longitude], 12);
                        if (marker) map.removeLayer(marker);
                        marker = L.marker([latitude, longitude]).addTo(map);
                        document.getElementById('lat').value = latitude;
                        document.getElementById('lng').value = longitude;
                    },
                    (error) => {
                        console.log("Error getting location:", error.message);
                    }
                );
            }
        }

        function setupFileInput() {
            const fileInput = document.querySelector('.file-input');
            const fileLabel = document.querySelector('.file-input-label span');

            if (fileInput) {
                fileInput.addEventListener('change', function() {
                    if (this.files && this.files[0]) {
                        fileLabel.textContent = this.files[0].name;
                    } else {
                        fileLabel.textContent = 'Select or take a photo';
                    }
                });
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            setupFileInput();
            initializeMap();
        });