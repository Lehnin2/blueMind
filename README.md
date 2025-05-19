# FishHealth - Fish Disease Detection System

This project is a fish disease detection application that allows users to upload images of fish and get predictions about their health status using computer vision models.

## Project Overview

The application consists of two parts:

1. **React Native Frontend**: A mobile/web app built with React Native and Expo that allows users to take photos, upload images, and view prediction results.

2. **Flask Backend API**: A Python API that uses PyTorch models to analyze fish images and detect diseases.

## How It Works

Instead of trying to run PyTorch models directly in JavaScript (which is challenging), we've implemented a client-server architecture:

1. The React Native app captures/uploads images and sends them to the backend API
2. The Flask API processes the images using PyTorch models
3. The prediction results are returned to the app and displayed to the user

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:

```bash
cd backend
```

2. Place your PyTorch model files in the backend directory:
   - `vit_fish_disease.pth` - Classifies whether the fish is healthy or sick
   - `classe.pth` - Classifies the type of disease if the fish is sick

3. Create a virtual environment and install dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

4. Start the backend server:

```bash
python app.py
```

The server will run at `http://localhost:5000` by default.

### Frontend Setup

1. Make sure you're in the project root directory

2. Update the API endpoint in `services/api.ts` to point to your backend:
   - For local development, use your machine's IP address instead of `localhost`
   - For deployment, use your deployed API URL

3. Install dependencies:

```bash
npm install
```

4. Start the app:

```bash
npm run dev
```

## Using the App

1. Launch the app on your device or emulator
2. Use the "Take Photo" or "Select Images" options to provide fish images
3. View the analysis results showing:
   - Health status (healthy or sick)
   - Disease type (if sick)
   - Disease information (description, symptoms, causes, treatments)

## Technology Stack

- **Frontend**:
  - React Native with Expo
  - TypeScript
  - Expo Router for navigation
  - Axios for API calls

- **Backend**:
  - Flask web framework
  - PyTorch for running machine learning models
  - Vision Transformer (ViT) models for image classification
  - Docker for containerization (optional)

## Models

The application uses two pre-trained Vision Transformer (ViT) models:

1. **vit_fish_disease.pth** - A binary classifier that determines if a fish is healthy or sick
2. **classe.pth** - A multi-class classifier that identifies the specific disease if a fish is sick

## Deployment

### Backend Deployment

The backend can be deployed using Docker to platforms like:
- Heroku
- Google Cloud Run
- AWS Elastic Beanstalk

See the backend README for detailed deployment instructions.

### Frontend Deployment

The React Native app can be deployed to:
- App stores (iOS, Android)
- Web (using Expo's web export)

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests. 
