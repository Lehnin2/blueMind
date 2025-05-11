# Fish Disease Detection Backend API

This is the backend API for the EcoPêche Fish Disease Detection app. It uses PyTorch and Flask to serve predictions from trained Vision Transformer (ViT) models.

## Setup

1. Place the PyTorch model files in the same directory as app.py:
   - `vit_fish_disease.pth` - Classifies whether the fish is healthy or sick
   - `classe.pth` - Classifies the type of disease if the fish is sick

2. Create a virtual environment and install dependencies:

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

3. Start the server:

```bash
python app.py
```

The server will run at `http://localhost:5000` by default.

## API Endpoints

### Health Check
- `GET /api/healthcheck`
  - Returns server status

### Disease Prediction
- `POST /api/predict`
  - Accepts either a file upload (`file`) or a base64-encoded image (`imageBase64`)
  - Returns prediction results in JSON format

## Example Response

```json
{
  "isHealthy": false,
  "confidence": 0.95,
  "diseaseType": "Bacterial Red disease",
  "description": "A bacterial infection that causes red lesions and inflammation on the fish body.",
  "symptoms": ["Red lesions", "Inflammation", "Loss of appetite", "Lethargy"],
  "causes": ["Aeromonas bacteria", "Poor water quality", "Stress", "Overcrowding"],
  "treatments": ["Antibiotics", "Water quality improvement", "Salt baths", "Isolation of affected fish"]
}
```

## Deployment

### Running with Docker

1. Build the Docker image:

```bash
docker build -t fish-disease-api .
```

2. Run the container:

```bash
docker run -p 5000:5000 fish-disease-api
```

### Deploying to Cloud

This API can be deployed to cloud platforms like:
- Heroku
- Google Cloud Run 
- AWS Elastic Beanstalk

For production deployments, make sure to:
1. Set `debug=False` in app.py
2. Configure proper security headers and CORS settings
3. Use environment variables for sensitive information
4. Consider adding authentication for API access 