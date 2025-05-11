from PIL import Image
import torch
import torchvision.transforms as transforms
import numpy as np

# Define the image transformation (matching the model input requirements)
transform = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize for ViT
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

def transform_image(image_path):
    """
    Takes an image path and transforms the image to the format required for ViT model.
    """
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0)  # Add batch dimension
    return image

def predict_health(image_path, health_model, device):
    """
    Predict if the fish is healthy or sick.
    Returns "Healthy" or "Sick".
    """
    image = transform_image(image_path)
    image = image.to(device)

    with torch.no_grad():
        output = health_model(image)
        probabilities = torch.nn.functional.softmax(output, dim=1)
        _, predicted = torch.max(output, 1)

    # Classes are ['healthy-fish', 'sick-fish'], so 0 is healthy, 1 is sick
    return "Healthy" if predicted.item() == 0 else "Sick"

def predict_disease(image_path, disease_model, device):
    """
    Predict the specific type of disease if the fish is sick.
    Returns the disease class name.
    """
    image = transform_image(image_path)
    image = image.to(device)

    # Disease classes
    disease_classes = [
        'Bacterial Red disease', 
        'Bacterial diseases - Aeromoniasis', 
        'Bacterial gill disease', 
        'Fungal diseases Saprolegniasis', 
        'Parasitic diseases', 
        'Viral diseases White tail disease'
    ]

    with torch.no_grad():
        output = disease_model(image)
        probabilities = torch.nn.functional.softmax(output, dim=1)
        _, predicted = torch.max(output, 1)
    
    return disease_classes[predicted.item()]

def get_confidence(output, class_idx):
    """
    Extract confidence score for a predicted class.
    """
    probabilities = torch.nn.functional.softmax(output, dim=1)
    return probabilities[0][class_idx].item() 