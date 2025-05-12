// Voice Assistant Component
class VoiceAssistant {
    constructor() {
        this.isListening = false;
        this.isSpeaking = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.createVoiceAssistantElement();
        this.initializeSpeechRecognition();
        this.initializeEventListeners();
    }

    createVoiceAssistantElement() {
        // Create voice assistant container
        const voiceContainer = document.createElement('div');
        voiceContainer.id = 'voice-assistant';
        voiceContainer.innerHTML = `
            <div class="voice-button" id="voice-button">
                <i class="bi bi-mic"></i>
            </div>
            <div class="voice-animation" id="voice-animation">
                <div class="circle-pulse"></div>
                <div class="wave-container">
                    <div class="wave"></div>
                    <div class="wave"></div>
                    <div class="wave"></div>
                    <div class="wave"></div>
                    <div class="wave"></div>
                </div>
            </div>
        `;
        document.body.appendChild(voiceContainer);

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            #voice-assistant {
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 1000;
                font-family: 'Inter', sans-serif;
            }

            .voice-button {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: #8B4513;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15), 0 0 0 2px rgba(205, 133, 63, 0.5);
                transition: all 0.3s ease;
                z-index: 1050;
                position: relative;
            }

            .voice-button i {
                color: white;
                font-size: 24px;
            }

            .voice-button:hover {
                transform: scale(1.1);
                background: #A0522D;
            }
            
            .voice-button.listening {
                background: #CD5C5C;
                animation: pulse 1.5s infinite;
            }
            
            .voice-button.speaking {
                background: #4682B4;
                animation: pulse 1.5s infinite;
            }
            
            @keyframes pulse {
                0% {
                    box-shadow: 0 0 0 0 rgba(205, 92, 92, 0.6);
                }
                70% {
                    box-shadow: 0 0 0 15px rgba(205, 92, 92, 0);
                }
                100% {
                    box-shadow: 0 0 0 0 rgba(205, 92, 92, 0);
                }
            }
            
            .voice-animation {
                position: absolute;
                bottom: 80px;
                left: 10px;
                width: 40px;
                height: 40px;
                display: none;
                align-items: center;
                justify-content: center;
            }
            
            .circle-pulse {
                position: absolute;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                background: rgba(139, 69, 19, 0.2);
                animation: circle-pulse 2s infinite;
            }
            
            @keyframes circle-pulse {
                0% {
                    transform: scale(0.95);
                    opacity: 0.7;
                }
                50% {
                    transform: scale(1.05);
                    opacity: 0.3;
                }
                100% {
                    transform: scale(0.95);
                    opacity: 0.7;
                }
            }
            
            .wave-container {
                position: absolute;
                width: 100%;
                height: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .wave {
                background: #CD853F;
                height: 100%;
                width: 3px;
                margin: 0 1px;
                border-radius: 5px;
                animation: wave 1s infinite ease-in-out;
            }
            
            .wave:nth-child(2) {
                animation-delay: 0.1s;
            }
            
            .wave:nth-child(3) {
                animation-delay: 0.2s;
            }
            
            .wave:nth-child(4) {
                animation-delay: 0.3s;
            }
            
            .wave:nth-child(5) {
                animation-delay: 0.4s;
            }
            
            @keyframes wave {
                0%, 100% {
                    height: 20%;
                }
                50% {
                    height: 80%;
                }
            }
        `;
        document.head.appendChild(style);
    }

    initializeSpeechRecognition() {
        if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'fr-FR';
            
            this.recognition.onstart = () => {
                this.isListening = true;
                this.updateUI();
                console.log('Reconnaissance vocale démarrée');
            };
            
            this.recognition.onend = () => {
                this.isListening = false;
                this.updateUI();
                console.log('Reconnaissance vocale terminée');
            };
            
            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                console.log('Vous avez dit:', transcript);
                this.processVoiceCommand(transcript);
            };
            
            this.recognition.onerror = (event) => {
                console.error('Erreur de reconnaissance vocale:', event.error);
                this.isListening = false;
                this.updateUI();
                this.speak('Désolé, je n\'ai pas pu comprendre. Veuillez réessayer.');
            };
        } else {
            console.error('La reconnaissance vocale n\'est pas prise en charge par ce navigateur.');
        }
    }

    initializeEventListeners() {
        const voiceButton = document.getElementById('voice-button');
        voiceButton.addEventListener('click', () => this.toggleListening());
    }

    toggleListening() {
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }

    startListening() {
        if (this.recognition) {
            try {
                this.recognition.start();
            } catch (error) {
                console.error('Erreur au démarrage de la reconnaissance vocale:', error);
            }
        }
    }

    stopListening() {
        if (this.recognition) {
            try {
                this.recognition.stop();
            } catch (error) {
                console.error('Erreur à l\'arrêt de la reconnaissance vocale:', error);
            }
        }
    }

    async processVoiceCommand(command) {
        try {
            // Envoyer la commande vocale au backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `message=${encodeURIComponent(command)}`
            });

            if (!response.ok) throw new Error('Erreur réseau');

            const data = await response.json();
            
            // Lire la réponse à haute voix
            this.speak(data.response || data.message);
        } catch (error) {
            console.error('Erreur:', error);
            this.speak('Désolé, une erreur est survenue. Veuillez réessayer.');
        }
    }

    speak(text) {
        if ('speechSynthesis' in window) {
            this.isSpeaking = true;
            this.updateUI();
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'fr-FR';
            
            utterance.onend = () => {
                this.isSpeaking = false;
                this.updateUI();
            };
            
            this.synthesis.speak(utterance);
        } else {
            console.error('La synthèse vocale n\'est pas prise en charge par ce navigateur.');
        }
    }

    updateUI() {
        const voiceButton = document.getElementById('voice-button');
        const voiceAnimation = document.getElementById('voice-animation');
        
        // Mettre à jour le bouton
        voiceButton.classList.remove('listening', 'speaking');
        if (this.isListening) {
            voiceButton.classList.add('listening');
            voiceButton.querySelector('i').className = 'bi bi-mic-fill';
        } else if (this.isSpeaking) {
            voiceButton.classList.add('speaking');
            voiceButton.querySelector('i').className = 'bi bi-volume-up-fill';
        } else {
            voiceButton.querySelector('i').className = 'bi bi-mic';
        }
        
        // Afficher/masquer l'animation
        if (this.isListening || this.isSpeaking) {
            voiceAnimation.style.display = 'flex';
        } else {
            voiceAnimation.style.display = 'none';
        }
    }
}

// Initialize voice assistant when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Vérifier si l'assistant vocal n'a pas déjà été initialisé
    if (!window.voiceAssistantInstance) {
        window.voiceAssistantInstance = new VoiceAssistant();
        console.log('Assistant vocal initialisé');
    }
});