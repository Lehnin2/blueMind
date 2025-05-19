# AquaSense – Smart Fish Identification & Marine Anomaly Detection

## Overview

AquaSense is an AI-powered platform for smart fish detection, species recognition, size and weight estimation, freshness and toxicity analysis, and marine anomaly detection. It also features a conversational chatbot that responds to marine-related queries in Tunisian dialect.

Built using a client-server architecture, AquaSense integrates computer vision, keypoint detection, and natural language processing to deliver a complete marine AI solution via a React Native frontend and FastAPI backend.

---

## Features

### 🐟 Fish Detection & Classification
- **Detectron2** for high-precision segmentation and classification.
- **YOLOv8s** optimized for mobile use.
- **Faster-RCNN (ResNet-50 FPN)** for challenging underwater environments.
- **YOLOv11s** for enhanced real-time performance in dynamic scenes.

### 📏 Fish Length, Size & Weight Estimation
- **YOLOv8n-Pose** for keypoint-based measurement (e.g., head-to-tail).
- **Tunisian Coin-Based Scaling** for converting pixel lengths to real-world sizes.
- **Random Forest Regressor** to predict fish weight from species and length.

### 🧊 Fish Freshness & Toxicity Detection
- **YOLOv8n** to assess freshness from visual features.
- **MobileNetV2** to classify toxic vs. non-toxic species.

### 🤖 Conversational AI Assistant – BlueMind Chatbot
- Based on **Deep Attention Matching (DAM)** architecture.
- Responds to questions on:
  - Fishing techniques
  - Species identification
  - Weather conditions
  - Legal and conservation topics

### 🔍 Smart Search for Protected & Invasive Species
- **Multi-Agent System** for name recognition and correction.
- **Groq AI + FAISS** for semantic search and matching.
- Integrates **YouTube API** and biodiversity data for:
  - Biological status (protected/invasive)
  - Cooking and educational videos

---

## Tech Stack

### Frontend
- **React Native**
- **TypeScript**
- **Expo**
- **Axios**

### Backend
- **FastAPI**
- **Uvicorn**
- **PyTorch**
- **Transformers**
- **Scikit-learn**

### Other Tools
- **Detectron2, YOLOv8, YOLOv11**
- **OpenCV**
- **MobileNetV2**
- **FAISS**
- **Groq AI**
- **YouTube Data API**
- **Custom Pose Dataset**
- **California Fish Weight Dataset**


---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Lehnin2/aquasense.git
cd aquasense

2. Backend Setup (FastAPI)
⚠️ Model files are not included in this repository due to size limits.
👉 Download models like model_fishonly_0016499.pth, model_final.pth, etc., from the GitHub Release.

cd backend
python -m venv venv
# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app:app --reload

MIT License – Free to use and adapt for non-commercial purposes.

Let me know if you'd like:
- A **French version** of this README  
- A **contribution guide** (`CONTRIBUTING.md`)  
- Or a **visual architecture diagram** to include in the repo.
