from flask import Flask, request, jsonify, render_template
import torch
import timm
from PIL import Image
import os
import io
import base64
from utils import transform_image, predict_health, predict_disease
from flask_cors import CORS
import google.generativeai as genai
import json
from dotenv import load_dotenv
from xai_utils import predict_and_explain, train_model

# Setup
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Uploads folder
UPLOAD_FOLDER = './static/uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# File paths (models are in the same directory as app.py)
health_model_path = 'vit_fish_disease.pth'
disease_model_path = 'classe.pth'

# Check if models exist
if not os.path.exists(health_model_path):
    raise FileNotFoundError(f"Health model not found at {health_model_path}")
if not os.path.exists(disease_model_path):
    raise FileNotFoundError(f"Disease model not found at {disease_model_path}")

# Load models
health_model = timm.create_model("vit_base_patch16_224", pretrained=False, num_classes=2)
health_model.load_state_dict(torch.load(health_model_path, map_location=torch.device('cpu')))
health_model.eval()

disease_model = timm.create_model("vit_base_patch16_224", pretrained=False, num_classes=6)
disease_model.load_state_dict(torch.load(disease_model_path, map_location=torch.device('cpu')))
disease_model.eval()

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
health_model.to(device)
disease_model.to(device)

# Disease information
disease_info = {
    'Bacterial Red disease': {
        'description': 'A bacterial infection that causes red lesions and inflammation on the fish body.',
        'symptoms': ['Red lesions', 'Inflammation', 'Loss of appetite', 'Lethargy'],
        'causes': ['Aeromonas bacteria', 'Poor water quality', 'Stress', 'Overcrowding'],
        'treatments': ['Antibiotics', 'Water quality improvement', 'Salt baths', 'Isolation of affected fish']
    },
    'Bacterial diseases - Aeromoniasis': {
        'description': 'A common bacterial infection causing ulcers, fin rot, and hemorrhages.',
        'symptoms': ['Ulcers', 'Fin rot', 'Hemorrhages', 'Dropsy', 'Exophthalmia'],
        'causes': ['Aeromonas bacteria', 'Injured tissue', 'Stress', 'Temperature fluctuations'],
        'treatments': ['Antibacterial treatments', 'Improved water quality', 'Reduced stocking density', 'Proper nutrition']
    },
    'Bacterial gill disease': {
        'description': 'A condition affecting the gills, causing respiratory distress and gill tissue damage.',
        'symptoms': ['Respiratory distress', 'Gill inflammation', 'Rapid gill movement', 'Reduced activity'],
        'causes': ['Flavobacterium bacteria', 'Poor water quality', 'High ammonia levels', 'Overcrowding'],
        'treatments': ['Antibiotic treatment', 'Improved aeration', 'Water changes', 'Reduced feeding']
    },
    'Fungal diseases Saprolegniasis': {
        'description': 'A fungal infection characterized by cotton-like growths on the skin, fins, and gills.',
        'symptoms': ['Cotton-like growths', 'Discolored patches', 'Lethargy', 'Loss of balance'],
        'causes': ['Saprolegnia fungi', 'Weakened immune system', 'Physical injury', 'Stress'],
        'treatments': ['Antifungal treatments', 'Salt baths', 'Improved water quality', 'Removal of dead tissue']
    },
    'Parasitic diseases': {
        'description': 'Various parasitic infections that can affect fish internally or externally.',
        'symptoms': ['Scratching against objects', 'White spots', 'Rapid breathing', 'Weight loss'],
        'causes': ['Various parasite species', 'Introduction of infected fish', 'Poor water quality', 'Overcrowding'],
        'treatments': ['Antiparasitic medications', 'Salt treatments', 'Copper sulfate (with caution)', 'Tank cleaning']
    },
    'Viral diseases White tail disease': {
        'description': 'A viral infection primarily affecting the tail, causing whitening and tissue damage.',
        'symptoms': ['White tail', 'Tail rot', 'Reduced growth', 'Mortality'],
        'causes': ['WSSV virus', 'Stress', 'Poor biosecurity', 'Temperature changes'],
        'treatments': ['No known cure', 'Prevention through biosecurity', 'Isolation of affected fish', 'Maintaining optimal water conditions']
    }
}

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key="AIzaSyC0cwIi4cXEH5iy0IMWquFK3Xf2SAcioUk")

# Create a chat session with the Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

# Load fish disease data
def load_fish_diseases():
    with open('data/fish_diseases.json', 'r') as file:
        return json.load(file)

# Create a context from the fish disease data
def create_context():
    diseases_data = load_fish_diseases()
    
    # Base prompt with instructions
    context = """You are a specialized Fish Disease Assistant. Your role is to provide accurate information about fish diseases, their symptoms, causes, treatments, and prevention methods. 
    You should ONLY answer questions related to fish diseases, fish health, and aquarium care. If asked about topics outside this scope, politely inform the user that you can only discuss fish diseases and related topics.
    
    Here is the information about common fish diseases that you can reference:
    
    """
    
    # Add disease information
    for disease in diseases_data['diseases']:
        context += f"\nDisease: {disease['name']}\n"
        context += f"Symptoms: {', '.join(disease['symptoms'])}\n"
        context += f"Causes: {disease['causes']}\n"
        context += f"Regions: {', '.join(disease['regions'])}\n"
        context += f"Treatment: {disease['treatment']}\n"
    
    # Add additional instructions
    context += """
    
    Guidelines for responses:
    1. Always stay focused on fish diseases and related topics
    2. If you don't know the answer, say so
    3. Be clear and concise in your explanations
    4. Use the provided disease information as your primary source
    5. If asked about topics outside fish diseases, respond with: "I'm sorry, but I can only provide information about fish diseases and related topics. Please ask me about fish diseases, their symptoms, causes, or treatments."
    
    Now, how can I help you with fish diseases today?
    """
    
    return context

# Initialize chat with context
chat = model.start_chat(history=[])
initial_context = create_context()
chat.send_message(initial_context)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get response from Gemini
        response = chat.send_message(user_message)
        
        return jsonify({
            'response': response.text
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/diseases', methods=['GET'])
def get_diseases():
    try:
        diseases_data = load_fish_diseases()
        return jsonify(diseases_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({"status": "healthy", "message": "Fish disease detection API is running"})

@app.route('/api/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        try:
            # Check if file is in request
            if 'file' in request.files:
                uploaded_file = request.files['file']
                if uploaded_file.filename != '':
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
                    uploaded_file.save(file_path)
                    image_path = file_path
                
            # Check if base64 image is in request
            elif 'imageBase64' in request.json:
                img_data = request.json['imageBase64']
                # Remove potential data URL prefix
                if ',' in img_data:
                    img_data = img_data.split(',')[1]
                
                img_bytes = base64.b64decode(img_data)
                img = Image.open(io.BytesIO(img_bytes))
                
                # Save image temporarily
                temp_filename = f"temp_{os.urandom(4).hex()}.jpg"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
                img.save(file_path)
                image_path = file_path
            else:
                return jsonify({'error': 'No image provided'}), 400
            
            # Predict health status
            health_status = predict_health(image_path, health_model, device)
            
            # Initialize response
            response = {
                'isHealthy': health_status == "Healthy",
                'confidence': 0.95  # Placeholder confidence value
            }
            
            # If sick, predict disease type
            if health_status == "Sick":
                disease_type = predict_disease(image_path, disease_model, device)
                response['diseaseType'] = disease_type
                
                # Add disease information
                if disease_type in disease_info:
                    response.update(disease_info[disease_type])
            
            return jsonify(response)
            
        except Exception as e:
            print(f"Error during prediction: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Method not allowed'}), 405

@app.route('/api/xai/predict', methods=['POST'])
def xai_predict():
    """Endpoint for explainable AI disease prediction."""
    if request.method == 'POST':
        try:
            # Get features from request
            features = request.json
            
            if not features:
                return jsonify({'error': 'No features provided'}), 400
            
            # Train model once and reuse (or load from cache in future)
            model_data = train_model()
            
            # Make prediction and generate explanations
            results = predict_and_explain(
                features=features,
                model_data=model_data,
                gemini_api_key="AIzaSyC0cwIi4cXEH5iy0IMWquFK3Xf2SAcioUk"
            )
            
            return jsonify(results)
            
        except Exception as e:
            print(f"Error during XAI prediction: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Method not allowed'}), 405

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 