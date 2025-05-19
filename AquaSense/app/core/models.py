import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from configz import settings

# Global variables for models and data
model = None
index = None
fish_data = []
texts = []
metadata = []

def initialize_models():
    """Initialize the SentenceTransformer model, FAISS index and load fish data"""
    global model, index, fish_data, texts, metadata
    
    # Load SentenceTransformer model
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    
    # Load fish data
    with open(settings.DATA_PATH, "r", encoding="utf-8") as f:
        fish_data = json.load(f)
    
    # Prepare data for FAISS search
    for item in fish_data:
        for name in [item["nom_tunisien"], item["nom_francais"], item["nom_scientifique"]]:
            if name:
                texts.append(name.lower())
                metadata.append(item)
    
    # Encode text data and create FAISS index
    embeddings = model.encode(texts, show_progress_bar=True)
    dim = embeddings[0].shape[0]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype("float32"))
    
    print(f"Models initialized: {len(fish_data)} fish entries loaded.")

def get_model():
    """Return the SentenceTransformer model"""
    return model

def get_index():
    """Return the FAISS index"""
    return index

def get_metadata():
    """Return the metadata list"""
    return metadata

def get_texts():
    """Return the texts list"""
    return texts

def get_fish_data():
    """Return the full fish data"""
    return fish_data