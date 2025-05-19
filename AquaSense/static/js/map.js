    // Initialize map
    const map = L.map('map').setView([34.0, 9.0], 6);
    
    // Add tile layer (map background)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Sample data - replace with {{ catches | tojson }} in production
    const catches = [
      {
        id: 1,
        species: "Sea Bass",
        length: 45,
        weight: 780,
        date: "2025-03-15",
        location: "Mediterranean Coast",
        lat: 35.5,
        lng: 11.2
      },
      {
        id: 2,
        species: "Tuna",
        length: 120,
        weight: 25000,
        date: "2025-04-02",
        location: "Deep Sea",
        lat: 33.8,
        lng: 10.1
      },
      {
        id: 3,
        species: "Bream",
        length: 28,
        weight: 350,
        date: "2025-04-12",
        location: "Coastal Waters",
        lat: 34.3,
        lng: 8.7
      },
      {
        id: 4,
        species: "Sea Bass",
        length: 52,
        weight: 950,
        date: "2025-05-01",
        location: "Rocky Shore",
        lat: 34.9,
        lng: 9.8
      }
    ];
    
    // In production, uncomment this line and comment out the sample data above
    // const catches = {{ catches | tojson }};
    
    // Create markers for all catches
    const markers = [];
    const markerLayer = L.layerGroup().addTo(map);
    
    function createMarkers(catchesData) {
      // Clear existing markers
      markerLayer.clearLayers();
      markers.length = 0;
      
      catchesData.forEach(catch_item => {
        const popupContent = `
          <div class="popup-header">
            <div class="popup-title">${catch_item.species}</div>
            <div class="popup-subtitle">${catch_item.location || 'Unknown location'}</div>
          </div>
          <div class="popup-details">
            <div class="popup-detail-item">
              <span class="popup-detail-label">Length:</span>
              <span class="popup-detail-value">${catch_item.length} cm</span>
            </div>
            <div class="popup-detail-item">
              <span class="popup-detail-label">Weight:</span>
              <span class="popup-detail-value">${catch_item.weight} g</span>
            </div>
            <div class="popup-detail-item">
              <span class="popup-detail-label">Date:</span>
              <span class="popup-detail-value">${formatDate(catch_item.date)}</span>
            </div>
          </div>
        `;
        
        const marker = L.marker([catch_item.lat, catch_item.lng])
          .bindPopup(popupContent, { className: 'custom-popup' });
        
        markers.push(marker);
        markerLayer.addLayer(marker);
      });
    }
    
    // Format date for display
    function formatDate(dateString) {
      if (!dateString) return 'Unknown';
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    }
    
    // Initialize filter panel functionality
    document.getElementById('showFilters').addEventListener('click', () => {
      document.getElementById('filterPanel').classList.add('active');
    });
    
    document.getElementById('closeFilters').addEventListener('click', () => {
      document.getElementById('filterPanel').classList.remove('active');
    });
    
    // Center map button functionality
    document.getElementById('centerMap').addEventListener('click', () => {
      if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
      } else {
        map.setView([34.0, 9.0], 6);
      }
    });
    
    // Populate species filter dropdown
    function populateSpeciesFilter(catchesData) {
      const speciesSet = new Set();
      catchesData.forEach(catch_item => {
        if (catch_item.species) {
          speciesSet.add(catch_item.species);
        }
      });
      
      const speciesFilter = document.getElementById('speciesFilter');
      speciesFilter.innerHTML = '<option value="">All Species</option>';
      
      Array.from(speciesSet).sort().forEach(species => {
        const option = document.createElement('option');
        option.value = species;
        option.textContent = species;
        speciesFilter.appendChild(option);
      });
    }
    
    // Filter functionality
    document.getElementById('applyFilters').addEventListener('click', () => {
      const species = document.getElementById('speciesFilter').value;
      const minLength = parseFloat(document.getElementById('minLengthFilter').value) || 0;
      const minWeight = parseFloat(document.getElementById('minWeightFilter').value) || 0;
      const dateRange = document.getElementById('dateRangeFilter').value;
      
      const filteredCatches = catches.filter(catch_item => {
        // Filter by species
        if (species && catch_item.species !== species) return false;
        
        // Filter by length
        if (minLength > 0 && catch_item.length < minLength) return false;
        
        // Filter by weight
        if (minWeight > 0 && catch_item.weight < minWeight) return false;
        
        // Filter by date
        if (dateRange !== 'all' && catch_item.date) {
          const catchDate = new Date(catch_item.date);
          const now = new Date();
          
          if (dateRange === 'month' && (now - catchDate) > 30 * 24 * 60 * 60 * 1000) return false;
          if (dateRange === 'quarter' && (now - catchDate) > 90 * 24 * 60 * 60 * 1000) return false;
          if (dateRange === 'year' && (now - catchDate) > 365 * 24 * 60 * 60 * 1000) return false;
        }
        
        return true;
      });
      
      createMarkers(filteredCatches);
      updateStatistics(filteredCatches);
      
      // Close the filter panel
      document.getElementById('filterPanel').classList.remove('active');
      
      // Center the map on the filtered markers
      if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
      }
    });
    
    // Update statistics panel
    function updateStatistics(catchesData) {
      document.getElementById('totalCatches').textContent = catchesData.length;
      
      // Find top species
      if (catchesData.length > 0) {
        const speciesCounts = {};
        catchesData.forEach(catch_item => {
          if (catch_item.species) {
            speciesCounts[catch_item.species] = (speciesCounts[catch_item.species] || 0) + 1;
          }
        });
        
        let topSpecies = '';
        let maxCount = 0;
        
        for (const species in speciesCounts) {
          if (speciesCounts[species] > maxCount) {
            maxCount = speciesCounts[species];
            topSpecies = species;
          }
        }
        
        document.getElementById('topSpecies').textContent = topSpecies || '-';
      } else {
        document.getElementById('topSpecies').textContent = '-';
      }
      
      // Find largest fish
      if (catchesData.length > 0) {
        let largestFish = catchesData.reduce((prev, current) => {
          return (prev.length > current.length) ? prev : current;
        });
        
        document.getElementById('largestFish').textContent = 
          `${largestFish.species} (${largestFish.length} cm)`;
      } else {
        document.getElementById('largestFish').textContent = '-';
      }
      
      // Find heaviest fish
      if (catchesData.length > 0) {
        let heaviestFish = catchesData.reduce((prev, current) => {
          return (prev.weight > current.weight) ? prev : current;
        });
        
        document.getElementById('heaviestFish').textContent = 
          `${heaviestFish.species} (${heaviestFish.weight} g)`;
      } else {
        document.getElementById('heaviestFish').textContent = '-';
      }
    }
    
    // Initialize the map with all catches
    createMarkers(catches);
    populateSpeciesFilter(catches);
    updateStatistics(catches);
    
    // Center map on all markers initially
    if (markers.length > 0) {
      const group = L.featureGroup(markers);
      map.fitBounds(group.getBounds().pad(0.1));
    }
