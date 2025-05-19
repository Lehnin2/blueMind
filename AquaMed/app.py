from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from inference_sdk import InferenceHTTPClient
import cv2
import os
import secrets
import numpy as np
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Crée le dossier d'upload si inexistant
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Clients Roboflow
# Client pour la classification santé/pathologie
HEALTH_CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="IieWdvhKidRl9uPqXx6U"
)

# Client pour la classification par type de coraux
TYPE_CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="TuCjLRoxKULEHrh7kV64"
)

# Simule une base de données utilisateurs
users_db = {
    "admin@aqua.com": {"password": "admin123", "role": "biologist"},
    "pharma@aqua.com": {"password": "pharma123", "role": "pharmacist"}
}

# Stockage temporaire des analyses
analyses_db = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        if email in users_db:
            flash('Email déjà enregistré!', 'error')
            return render_template('signup.html')
        
        users_db[email] = {"password": password, "role": role}
        flash('Inscription réussie! Vous pouvez vous connecter.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email in users_db and users_db[email]['password'] == password:
            session['user'] = email
            session['role'] = users_db[email]['role']
            flash('Connexion réussie!', 'success')
            return redirect(url_for('analyze'))
        else:
            flash('Email ou mot de passe incorrect!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Déconnexion réussie!', 'success')
    return redirect(url_for('index'))

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    # Vérifier si l'utilisateur est connecté
    if 'user' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Récupérer le type d'analyse sélectionné
        analysis_type = request.form.get('analysis_type')
        
        if not analysis_type:
            flash('Veuillez sélectionner un type d\'analyse!', 'error')
            return render_template('analyze.html')
        
        # Vérifier si un fichier a été envoyé
        if 'file' not in request.files:
            flash('Aucun fichier sélectionné!', 'error')
            return render_template('analyze.html')
        
        file = request.files['file']
        if file.filename == '':
            flash('Aucun fichier sélectionné!', 'error')
            return render_template('analyze.html')
        
        # Vérifier le type de fichier
        if file and allowed_file(file.filename):
            try:
                # Sauvegarder le fichier
                filename = secure_filename(file.filename)
                filename = f"{secrets.token_hex(8)}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Analyse selon le type sélectionné
                if analysis_type == 'pathology':
                    # Classification santé/pathologie SEULEMENT
                    health_model_id = "class-yenrt/1"
                    health_result = HEALTH_CLIENT.infer(filepath, model_id=health_model_id)
                    
                    # Traite l'image
                    image = cv2.imread(filepath)
                    if image is None:
                        flash('Erreur lors de la lecture de l\'image!', 'error')
                        return render_template('analyze.html')
                    
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    
                    # Extraction des résultats de classification santé
                    health_classification = "Non déterminé"
                    health_confidence = 0.0
                    
                    if "predictions" in health_result and health_result["predictions"]:
                        prediction = health_result["predictions"][0]
                        health_classification = prediction["class"]
                        health_confidence = prediction["confidence"]
                    
                    # Ajoute le texte sur l'image
                    health_color = (76, 175, 80) if health_confidence > 0.7 else (255, 193, 7) if health_confidence > 0.5 else (244, 67, 54)
                    health_text = f"État: {health_classification} ({health_confidence:.2f})"
                    cv2.putText(image, health_text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
                               1, health_color, 2, cv2.LINE_AA)
                    
                    # Sauvegarde l'image analysée
                    analyzed_filename = f"analyzed_{filename}"
                    analyzed_path = os.path.join(app.config['UPLOAD_FOLDER'], analyzed_filename)
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(analyzed_path, image_rgb)
                    
                    # Stocke l'analyse
                    analysis_id = secrets.token_hex(8)
                    analyses_db[analysis_id] = {
                        'user': session['user'],
                        'timestamp': datetime.now().isoformat(),
                        'analysis_type': 'pathology',
                        'health_classification': health_classification,
                        'health_confidence': health_confidence,
                        'image_path': filename,
                        'analyzed_path': analyzed_filename
                    }
                    
                    return redirect(url_for('view_pathology_analysis', id=analysis_id))
                
                elif analysis_type == 'type':
                    # Classification par type de coraux SEULEMENT
                    type_model_id = "corals_clasification-fvezg-k5oxw/1"
                    type_result = TYPE_CLIENT.infer(filepath, model_id=type_model_id)
                    
                    # Traite l'image
                    image = cv2.imread(filepath)
                    if image is None:
                        flash('Erreur lors de la lecture de l\'image!', 'error')
                        return render_template('analyze.html')
                    
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    
                    # Extraction des résultats de classification type
                    coral_type = "Non déterminé"
                    type_confidence = 0.0
                    
                    if "predictions" in type_result and type_result["predictions"]:
                        prediction = type_result["predictions"][0]
                        coral_type = prediction["class"]
                        type_confidence = prediction["confidence"]
                    
                    # Ajoute le texte sur l'image
                    type_color = (30, 144, 255)  # Bleu pour le type
                    type_text = f"Type: {coral_type} ({type_confidence:.2f})"
                    cv2.putText(image, type_text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
                               1, type_color, 2, cv2.LINE_AA)
                    
                    # Sauvegarde l'image analysée
                    analyzed_filename = f"analyzed_{filename}"
                    analyzed_path = os.path.join(app.config['UPLOAD_FOLDER'], analyzed_filename)
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(analyzed_path, image_rgb)
                    
                    # Stocke l'analyse
                    analysis_id = secrets.token_hex(8)
                    analyses_db[analysis_id] = {
                        'user': session['user'],
                        'timestamp': datetime.now().isoformat(),
                        'analysis_type': 'type',
                        'coral_type': coral_type,
                        'confidence': type_confidence,  # Note: utilise 'confidence' pour le template type
                        'image_path': filename,
                        'analyzed_path': analyzed_filename
                    }
                    
                    return redirect(url_for('view_type_analysis', id=analysis_id))
                    
            except Exception as e:
                flash(f'Erreur lors de l\'analyse: {str(e)}', 'error')
                return render_template('analyze.html')
    
    return render_template('analyze.html')

# Route pour afficher l'analyse pathologique
@app.route('/view_pathology_analysis/<id>')
def view_pathology_analysis(id):
    if 'user' not in session:
        flash('Veuillez vous connecter.', 'error')
        return redirect(url_for('login'))
    
    if id not in analyses_db:
        flash('Analyse non trouvée!', 'error')
        return redirect(url_for('analyze'))
    
    analysis = analyses_db[id]
    return render_template('view_pathology_analysis.html', analysis=analysis, id=id)

# Route pour afficher l'analyse de type
@app.route('/view_type_analysis/<id>')
def view_type_analysis(id):
    if 'user' not in session:
        flash('Veuillez vous connecter.', 'error')
        return redirect(url_for('login'))
    
    if id not in analyses_db:
        flash('Analyse non trouvée!', 'error')
        return redirect(url_for('analyze'))
    
    analysis = analyses_db[id]
    return render_template('view_type_analysis.html', analysis=analysis, id=id)

# Route générique (optionnelle) qui redirige vers le bon template
@app.route('/view_analysis/<id>')
def view_analysis(id):
    if 'user' not in session:
        flash('Veuillez vous connecter.', 'error')
        return redirect(url_for('login'))
    
    if id not in analyses_db:
        flash('Analyse non trouvée!', 'error')
        return redirect(url_for('analyze'))
    
    analysis = analyses_db[id]
    
    # Redirige vers le bon template selon le type d'analyse
    if 'analysis_type' in analysis:
        if analysis['analysis_type'] == 'pathology':
            return redirect(url_for('view_pathology_analysis', id=id))
        elif analysis['analysis_type'] == 'type':
            return redirect(url_for('view_type_analysis', id=id))
    
    # Si le type n'est pas spécifié, essaie de deviner
    if 'health_classification' in analysis:
        return redirect(url_for('view_pathology_analysis', id=id))
    elif 'coral_type' in analysis:
        return redirect(url_for('view_type_analysis', id=id))
    
    # Fallback
    flash('Type d\'analyse non reconnu!', 'error')
    return redirect(url_for('analyze'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

if __name__ == '__main__':
    app.run(debug=True)