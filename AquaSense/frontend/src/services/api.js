const API_BASE_URL = 'http://localhost:8000';

export const weatherService = {
    getCurrentWeather: async (coordinates) => {
        const response = await fetch(`${API_BASE_URL}/meteo/current/${coordinates}`);
        if (!response.ok) throw new Error('Weather data fetch failed');
        return response.json();
    },
    
    getForecast: async (coordinates) => {
        const response = await fetch(`${API_BASE_URL}/meteo/forecast/${coordinates}`);
        if (!response.ok) throw new Error('Forecast data fetch failed');
        return response.json();
    }
};

export const chatbotService = {
    sendMessage: async (message) => {
        const response = await fetch(`${API_BASE_URL}/chatbot/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        if (!response.ok) throw new Error('Chatbot request failed');
        return response.json();
    }
};

export const detectionService = {
    detect: async (data) => {
        const response = await fetch(`${API_BASE_URL}/detection`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Detection request failed');
        return response.json();
    }
};