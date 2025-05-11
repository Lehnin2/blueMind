from fastapi import APIRouter, Request, HTTPException
from app.tools_integration import get_depth_at_location
from app.tools.estimationProfondeur import obtenir_profondeur
import os

depth_api = APIRouter()

@depth_api.get("/api/depth")
async def get_depth_data(request: Request):
    """API endpoint pour obtenir la profondeur à une position donnée."""
    try:
        # Récupérer les coordonnées depuis les paramètres de requête
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        
        # Vérifier que les coordonnées sont valides
        if not lat or not lon:
            raise HTTPException(status_code=422, detail="Les paramètres lat et lon sont requis")
        
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            raise HTTPException(status_code=422, detail="Les coordonnées doivent être des nombres valides")
        
        # Essayer d'abord avec get_depth_at_location de tools_integration
        try:
            depth = get_depth_at_location(lat, lon)
        except Exception as e:
            # Si ça échoue, essayer avec obtenir_profondeur
            try:
                fichier_nc = os.path.join("C:\\", "Users", "user", "OneDrive", "Bureau", "multi-agent system", "data", "carte_marine_tunisie.nc")
                depth = obtenir_profondeur(fichier_nc, lat, lon)
            except Exception as e2:
                # Si les deux méthodes échouent, estimer la profondeur
                depth = estimate_depth_from_shore(lat, lon)
        
        # Si la profondeur est None, estimer la profondeur
        if depth is None:
            depth = estimate_depth_from_shore(lat, lon)
        
        return {"depth": depth, "lat": lat, "lon": lon}
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de la profondeur: {str(e)}")


def estimate_depth_from_shore(lat, lon):
    """Estimation de la profondeur basée sur la distance à la côte."""
    # Coordonnées approximatives de la côte tunisienne
    coast_points = [
        {"lat": 37.3, "lon": 9.8},  # Nord
        {"lat": 36.8, "lon": 10.3}, # Tunis
        {"lat": 35.8, "lon": 10.6}, # Sousse
        {"lat": 34.7, "lon": 10.8}, # Sfax
        {"lat": 33.9, "lon": 10.1}, # Gabès
        {"lat": 33.3, "lon": 11.2}  # Sud
    ]
    
    # Calcul de la distance minimale à la côte
    min_distance = float('inf')
    for point in coast_points:
        # Formule de Haversine pour calculer la distance
        R = 6371  # Rayon de la Terre en km
        dLat = (point["lat"] - lat) * 3.14159 / 180
        dLon = (point["lon"] - lon) * 3.14159 / 180
        a = (pow(dLat/2, 2) + 
             pow(dLon/2, 2) * 
             pow(3.14159/180 * lat, 2) * 
             pow(3.14159/180 * point["lat"], 2))
        c = 2 * 3.14159/180 * (a ** 0.5) * ((1-a) ** 0.5)
        distance = R * c
        
        if distance < min_distance:
            min_distance = distance
    
    # Modèle simplifié: 10m de profondeur par km depuis la côte, plafonné à 1500m
    return min(min_distance * 10, 1500)