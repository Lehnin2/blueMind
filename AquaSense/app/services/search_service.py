import numpy as np
from app.core.models import get_model, get_index, get_metadata
from configz import settings
from app.utils.helpers import is_arabic

def search_fish(query: str, k: int = settings.DEFAULT_TOP_K):
    """
    Search for fish using vector similarity.
    
    Args:
        query: The search query (fish name)
        k: Number of results to return
    
    Returns:
        List of fish entries that match the query
    """
    # Get model, index and metadata
    model = get_model()
    index = get_index()
    metadata = get_metadata()
    
    # Encode query
    query_vec = model.encode([query.lower()])
    
    # Search in FAISS index
    D, I = index.search(np.array(query_vec).astype("float32"), k)
    
    # Return metadata for the matching indices
    return [metadata[i] for i in I[0]]