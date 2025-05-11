# Comprehensive Tunisian Ports Database
TUNISIAN_PORTS = [
    # Jendouba Governorate
    {"name": "Port de Tabarka", "governorate": "Jendouba", "lat": 36.9558, "lon": 8.7339},
    
    # Monastir Governorate
    {"name": "Port de Monastir", "governorate": "Monastir", "lat": 35.7789, "lon": 10.8262},
    {"name": "Port de Sayada", "governorate": "Monastir", "lat": 35.6500, "lon": 11.0833},
    {"name": "Port de Ksibet Mediouni", "governorate": "Monastir", "lat": 35.5667, "lon": 11.0333},
    
    # Gabes Governorate
    {"name": "Port de Gabes", "governorate": "Gabes", "lat": 33.8869, "lon": 10.1082},
    {"name": "Port de Zarat", "governorate": "Gabes", "lat": 33.7333, "lon": 10.2667},
    
    # Bizerte Governorate
    {"name": "Port de Zarzouna", "governorate": "Bizerte", "lat": 37.2744, "lon": 9.8746},
    {"name": "Port de Ghar El Melh", "governorate": "Bizerte", "lat": 37.1667, "lon": 10.2167},
    {"name": "Port de Cap Zebib", "governorate": "Bizerte", "lat": 37.2333, "lon": 10.0500},
    {"name": "Port de Sidi Mechreg", "governorate": "Bizerte", "lat": 37.2333, "lon": 9.8000},
    
    # Medenine Governorate
    {"name": "Port de Zarzis", "governorate": "Medenine", "lat": 33.5039, "lon": 11.1172},
    {"name": "Port de Houmet Souk", "governorate": "Medenine", "lat": 33.9167, "lon": 10.8667},
    {"name": "Port d'Ajim", "governorate": "Medenine", "lat": 33.9500, "lon": 10.8167},
    {"name": "Port de Boughrara", "governorate": "Medenine", "lat": 33.7500, "lon": 10.9667},
    
    # Mahdia Governorate
    {"name": "Port de Mahdia", "governorate": "Mahdia", "lat": 35.5050, "lon": 11.0620},
    {"name": "Port de Chebba", "governorate": "Mahdia", "lat": 35.4333, "lon": 11.1167},
    {"name": "Port de Salakta", "governorate": "Mahdia", "lat": 35.5500, "lon": 11.0333},
    {"name": "Port de Malloulech", "governorate": "Mahdia", "lat": 35.5167, "lon": 11.0833},
    
    # Ariana Governorate
    {"name": "Port de Kalaat Landalous", "governorate": "Ariana", "lat": 36.8500, "lon": 10.3167},
    
    # Tunis Governorate
    {"name": "Port de la Goulette", "governorate": "Tunis", "lat": 36.8333, "lon": 10.3167},
    
    # Nabeul Governorate
    {"name": "Port de Kelibia", "governorate": "Nabeul", "lat": 36.8444, "lon": 11.0889},
    {"name": "Port de Beni Khiar", "governorate": "Nabeul", "lat": 36.7333, "lon": 10.8833},
    {"name": "Port de Haouaria", "governorate": "Nabeul", "lat": 36.8167, "lon": 10.9500},
    {"name": "Port de Sidi Daoud", "governorate": "Nabeul", "lat": 36.7500, "lon": 10.8833},
    
    # Sfax Governorate
    {"name": "Port de Sfax", "governorate": "Sfax", "lat": 34.7272, "lon": 10.7603},
    {"name": "Port de Mahres", "governorate": "Sfax", "lat": 34.5333, "lon": 10.5000},
    {"name": "Port de Skhira", "governorate": "Sfax", "lat": 34.3000, "lon": 10.1000},
    {"name": "Port de Kraten", "governorate": "Sfax", "lat": 34.6500, "lon": 10.6500},
    
    # Sousse Governorate
    {"name": "Port de Sousse", "governorate": "Sousse", "lat": 35.8272, "lon": 10.6356},
    {"name": "Port de Hergla", "governorate": "Sousse", "lat": 36.0333, "lon": 10.5000},
    {"name": "Port de Louza – Louata", "governorate": "Sousse", "lat": 35.8167, "lon": 10.6000},
    {"name": "Port de Zaboussa", "governorate": "Sousse", "lat": 35.8500, "lon": 10.6333},
    {"name": "Port d'El Aouabed", "governorate": "Sousse", "lat": 35.8333, "lon": 10.6167}
]

def get_ports_by_governorate(governorate):
    """
    Retrieve all ports for a specific governorate
    """
    return [port for port in TUNISIAN_PORTS if port['governorate'].lower() == governorate.lower()]

def find_nearest_port(lat, lon, governorate=None):
    """
    Find the nearest port, optionally filtered by governorate
    """
    import math
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r
    
    # Filter ports by governorate if specified
    ports_to_check = TUNISIAN_PORTS if governorate is None else \
        [port for port in TUNISIAN_PORTS if port['governorate'].lower() == governorate.lower()]
    
    # Find the nearest port
    return min(ports_to_check, key=lambda port: haversine_distance(lat, lon, port['lat'], port['lon']))

