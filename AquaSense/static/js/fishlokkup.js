const API_URL = '/api/v1';

document.getElementById('searchButton').addEventListener('click', searchFish);
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        searchFish();
    }
});

async function searchFish() {
    const query = document.getElementById('searchInput').value.trim();
    
    if (!query) {
        showError('Please enter a fish name to search');
        return;
    }
    
    const topK = parseInt(document.getElementById('resultsCount').value) || 3;
    const enhanceWithLlm = document.getElementById('enhanceResults').value === 'true';
    
    // Show loading, hide previous results
    document.getElementById('loading').style.display = 'block';
    document.getElementById('errorMessage').style.display = 'none';
    document.getElementById('resultsContainer').innerHTML = '';
    document.getElementById('noResults').style.display = 'none';
    document.getElementById('searchInfo').style.display = 'none';
    document.getElementById('searchInfo').textContent = '';
    
    try {
        const response = await fetch(`${API_URL}/fish/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                top_k: topK,
                enhance_with_llm: enhanceWithLlm
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('API Response:', data); // Debug: Log the full API response
        displayResults(data);
    } catch (error) {
        console.error('Error fetching data:', error);
        showError('Error searching for fish: ' + error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

function displayResults(data) {
    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.innerHTML = '';
    
    if (data.results && data.results.length > 0) {
        // Show search info
        const searchInfo = document.getElementById('searchInfo');
        if (data.corrected_query !== document.getElementById('searchInput').value.trim()) {
            searchInfo.textContent = `Showing results for: "${data.corrected_query}" (${data.count} result${data.count !== 1 ? 's' : ''})`;
        } else {
            searchInfo.textContent = `Found ${data.count} result${data.count !== 1 ? 's' : ''}`;
        }
        searchInfo.style.display = 'block';
        
        // Generate result cards
        data.results.forEach(fish => {
            console.log('Fish Data:', fish); // Debug: Log each fish object
            const card = document.createElement('div');
            card.className = 'fish-card fade-in';
            
            const header = document.createElement('div');
            header.className = 'fish-header';
            
            const names = document.createElement('div');
            names.className = 'fish-names';
            
            let primaryName = fish.nom_francais || fish.nom_tunisien || fish.nom_scientifique || 'Unknown';
            let secondaryName = '';
            
            if (fish.nom_tunisien && fish.nom_francais) {
                secondaryName = `${fish.nom_tunisien} / ${fish.nom_francais}`;
            } else if (fish.nom_tunisien) {
                secondaryName = fish.nom_tunisien;
            } else if (fish.nom_francais) {
                secondaryName = fish.nom_francais;
            }
            
            names.innerHTML = `
                <h2>${primaryName}</h2>
                ${secondaryName ? `<div>${secondaryName}</div>` : ''}
                ${fish.nom_scientifique ? `<div class="scientific">${fish.nom_scientifique}</div>` : ''}
            `;
            
            const status = document.createElement('div');
            status.className = 'fish-status';
            
            status.innerHTML = `
                <span class="status-badge ${fish.protected ? 'protected' : 'not-protected'}">
                    ${fish.protected ? '<i class="fas fa-shield-alt"></i> Protected' : '<i class="fas fa-check-circle"></i> Not Protected'}
                </span>
                <span class="status-badge ${fish.invasive ? 'invasive' : 'not-invasive'}">
                    ${fish.invasive ? '<i class="fas fa-exclamation-triangle"></i> Invasive' : '<i class="fas fa-check-circle"></i> Non-Invasive'}
                </span>
            `;
            
            header.appendChild(names);
            header.appendChild(status);
            
            const description = document.createElement('div');
            description.className = 'fish-description';
            description.textContent = fish.improved_description || 'No description available.';
            
            // Add main video section
            const videoSection = document.createElement('div');
            videoSection.className = 'fish-video';
            if (fish.video && fish.video.url) {
                const videoId = fish.video.url.split('v=')[1]?.split('&')[0];
                if (videoId) {
                    videoSection.innerHTML = `
                        <p><i class="fas fa-video me-2"></i> Watch a video: ${fish.video.title}</p>
                        <div class="video-container">
                            <iframe src="https://www.youtube.com/embed/${videoId}" 
                                    title="${fish.video.title}" 
                                    frameborder="0" 
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                    allowfullscreen></iframe>
                        </div>
                    `;
                } else {
                    videoSection.innerHTML = '<p><i class="fas fa-video-slash me-2"></i> No video available.</p>';
                }
            } else {
                videoSection.innerHTML = '<p><i class="fas fa-video-slash me-2"></i> No video available.</p>';
            }
            
            // Add recipe suggestions section
            const recipesSection = document.createElement('div');
            recipesSection.className = 'fish-recipes';
            recipesSection.innerHTML = '<h3><i class="fas fa-utensils me-2"></i>Recipe Suggestions</h3>';
            
            if (fish.recipe_suggestions && Array.isArray(fish.recipe_suggestions) && fish.recipe_suggestions.length > 0) {
                console.log('Recipe Suggestions:', fish.recipe_suggestions); // Debug: Log recipes
                fish.recipe_suggestions.forEach(recipe => {
                    const recipeItem = document.createElement('div');
                    recipeItem.className = 'recipe-item';
                    
                    const recipeName = recipe.name || 'Unknown Recipe';
                    const recipeDescription = recipe.description || 'No description available.';
                    
                    let recipeHTML = `
                        <h4>${recipeName}</h4>
                        <p>${recipeDescription}</p>
                    `;
                    
                    // Recipe video (if available)
                    if (recipe.video && recipe.video.url) {
                        const videoId = recipe.video.url.split('v=')[1]?.split('&')[0];
                        if (videoId) {
                            recipeHTML += `
                                <p><i class="fas fa-video me-2"></i> Watch recipe: ${recipe.video.title || 'Recipe Video'}</p>
                                <div class="video-container">
                                    <iframe src="https://www.youtube.com/embed/${videoId}" 
                                            title="${recipe.video.title || 'Recipe Video'}" 
                                            frameborder="0" 
                                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                            allowfullscreen></iframe>
                                </div>
                            `;
                        } else {
                            recipeHTML += '<p><i class="fas fa-video-slash me-2"></i> No recipe video available.</p>';
                        }
                    } else {
                        recipeHTML += '<p><i class="fas fa-video-slash me-2"></i> No recipe video available.</p>';
                    }
                    
                    recipeItem.innerHTML = recipeHTML;
                    recipesSection.appendChild(recipeItem);
                });
            } else {
                console.warn('No recipe suggestions found for fish:', primaryName); // Debug: Log missing recipes
                recipesSection.innerHTML += '<p>No recipe suggestions available.</p>';
            }
            
            card.appendChild(header);
            card.appendChild(description);
            card.appendChild(videoSection);
            card.appendChild(recipesSection);
            
            resultsContainer.appendChild(card);
        });
    } else {
        document.getElementById('noResults').style.display = 'block';
    }
}

function showError(message) {
    const errorElement = document.getElementById('errorMessage');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    document.getElementById('loading').style.display = 'none';
}