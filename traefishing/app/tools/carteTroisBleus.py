from PIL import Image, ImageDraw
import math
import cv2
import numpy as np
from typing import Tuple
import matplotlib.pyplot as plt
import os

# Convertisseurs entre degrés-minutes et décimal
def deg_min_to_decimal(deg: int, minutes: float) -> float:
    """Convertit des degrés et minutes en degrés décimaux."""
    return deg + minutes / 60

def decimal_to_deg_min(decimal_deg: float) -> tuple[int, float]:
    """Convertit des degrés décimaux en degrés et minutes."""
    deg = int(decimal_deg)
    minutes = (decimal_deg - deg) * 60
    return deg, minutes

def latlon_to_pixel_mercator(latitude, longitude, image_width, image_height, 
                           lon_min, lon_max, lat_min, lat_max):
    """
    Convertit lat/lon en coordonnées pixel avec projection Mercator.
    """
    lat_rad = math.radians(latitude)
    lat_min_rad = math.radians(lat_min)
    lat_max_rad = math.radians(lat_max)
    
    x_ratio = (longitude - lon_min) / (lon_max - lon_min)
    x_pixel = int(x_ratio * image_width)
    
    y_mercator = math.log(math.tan(math.pi/4 + lat_rad/2))
    y_mercator_min = math.log(math.tan(math.pi/4 + lat_min_rad/2))
    y_mercator_max = math.log(math.tan(math.pi/4 + lat_max_rad/2))
    
    y_ratio = (y_mercator_max - y_mercator) / (y_mercator_max - y_mercator_min)
    y_pixel = int(y_ratio * image_height)
    
    x_pixel = max(0, min(x_pixel, image_width - 1))
    y_pixel = max(0, min(y_pixel, image_height - 1))
    
    return (x_pixel, y_pixel)

def calculate_scale(image: np.ndarray, lat_range: tuple, lon_range: tuple, 
                    margin_left: int, margin_right: int, margin_top: int, margin_bottom: int) -> float:
    """Calcule l'échelle de conversion pixels -> kilomètres."""
    height, width = image.shape[:2]
    lat_min, lat_max = lat_range
    lon_min, lon_max = lon_range

    # Distance en degrés
    lat_diff = lat_max - lat_min  # en degrés
    lon_diff = lon_max - lon_min  # en degrés

    # Conversion en kilomètres
    lat_km = lat_diff * 111  # 1° latitude ≈ 111 km
    avg_lat = (lat_min + lat_max) / 2
    lon_km = lon_diff * 111 * math.cos(math.radians(avg_lat))

    # Échelle : km par pixel
    km_per_pixel_x = lon_km / (width - margin_left - margin_right)
    km_per_pixel_y = lat_km / (height - margin_top - margin_bottom)
    return (km_per_pixel_x + km_per_pixel_y) / 2

def create_color_mask(image: np.ndarray, color: Tuple[int, int, int]) -> np.ndarray:
    """Crée un masque pour une couleur donnée avec une tolérance."""
    tolerance = 50
    lower_bound = np.array([max(0, c - tolerance) for c in color], dtype=np.uint8)
    upper_bound = np.array([min(255, c + tolerance) for c in color], dtype=np.uint8)
    return cv2.inRange(image, lower_bound, upper_bound)

def process_image(image_path: str, zone_colors: dict) -> Tuple[np.ndarray, dict, dict]:
    """Traite l'image pour extraire les zones de couleur spécifiées."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Le fichier image n'existe pas : {image_path}")
    
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Erreur de chargement de l'image : {image_path}")
    
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_rgb = cv2.GaussianBlur(image_rgb, (5, 5), 0)
    
    # Dictionnaire pour stocker les contours de chaque zone
    zone_contours = {}
    masks = {}
    
    # Créer un masque et extraire les contours pour chaque couleur
    for zone_name, color in zone_colors.items():
        zone_mask = create_color_mask(image_rgb, color)
        kernel = np.ones((3, 3), np.uint8)
        zone_mask = cv2.morphologyEx(zone_mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(zone_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        zone_contours[zone_name] = [c for c in contours if cv2.contourArea(c) > 100]
        masks[zone_name] = zone_mask
        if zone_name != "terre":
            print(f"Nombre de contours détectés pour {zone_name} : {len(zone_contours[zone_name])}")
    
    return image, zone_contours, masks

def get_min_distance_to_contour(x: int, y: int, contours: list, km_per_pixel: float) -> float:
    """Calcule la distance minimale en kilomètres entre un point et les contours."""
    min_distance_pixels = float('inf')
    point = np.array([x, y])
    for contour in contours:
        for point_in_contour in contour:
            contour_point = point_in_contour[0]
            distance = np.linalg.norm(point - contour_point)
            min_distance_pixels = min(min_distance_pixels, distance)
    
    return min_distance_pixels * km_per_pixel

def get_nearest_zone(x: int, y: int, zone_contours: dict, km_per_pixel: float) -> Tuple[str, float]:
    """Trouve la zone la plus proche et la distance à sa frontière."""
    min_distance = float('inf')
    nearest_zone = None
    
    for zone_name, contours in zone_contours.items():
        if zone_name != "terre":  # On ne calcule pas la distance à la terre
            distance = get_min_distance_to_contour(x, y, contours, km_per_pixel)
            if distance < min_distance:
                min_distance = distance
                nearest_zone = zone_name
    
    return nearest_zone, min_distance

def is_point_in_zone(x: int, y: int, contours: list) -> bool:
    """Vérifie si le point est à l'intérieur des contours d'une zone."""
    point = (x, y)
    for contour in contours:
        if cv2.pointPolygonTest(contour, point, False) >= 0:
            return True
    return False

def check_location(image: np.ndarray, x: int, y: int, zone_colors: dict, zone_contours: dict, masks: dict, km_per_pixel: float) -> str:
    """Vérifie la position du bateau et génère des messages."""
    # Vérifier d'abord si le point est dans une zone en utilisant les contours
    zone_name = None
    for name, contours in zone_contours.items():
        if is_point_in_zone(x, y, contours):
            zone_name = name
            break
    
    # Si aucune zone n'est détectée via les contours, vérifier la couleur (pour la terre ou hors zone)
    if zone_name is None:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pixel_color = image_rgb[y, x]
        print(f"Couleur du pixel à ({x}, {y}) : {pixel_color}")
        
        tolerance = 50
        for name, color in zone_colors.items():
            if (abs(int(pixel_color[0]) - color[0]) <= tolerance and
                abs(int(pixel_color[1]) - color[1]) <= tolerance and
                abs(int(pixel_color[2]) - color[2]) <= tolerance):
                zone_name = name
                break
    
    # Générer le message en fonction de la zone
    if zone_name == "nord":
        status = "📍 Le bateau est dans la Zone Nord des eaux tunisiennes (zone de pêche réglementaire)."
    elif zone_name == "centre":
        status = "📍 Le bateau est dans la Zone Centre des eaux tunisiennes (zone de pêche réglementaire)."
    elif zone_name == "sud":
        status = "📍 Le bateau est dans la Zone Sud des eaux tunisiennes (zone de pêche réglementaire)."
    elif zone_name == "terre":
        status = "⚠️ Le bateau est sur la terre tunisienne (zone non navigable pour la pêche)."
    else:
        # Hors zone réglementaire (mer blanche)
        status = "⚠️ Le bateau est hors des zones de pêche réglementaires des eaux tunisiennes (zone blanche)."
        # Trouver la zone la plus proche
        nearest_zone, distance = get_nearest_zone(x, y, zone_contours, km_per_pixel)
        status += f"\nLa zone réglementaire la plus proche est la Zone {nearest_zone.capitalize()} à {distance:.2f} km."
        if distance <= 0.5:
            status += "\n⚠️ ATTENTION : Le bateau est très proche de la frontière d'une zone réglementaire. Veuillez ajuster votre trajectoire si nécessaire."
    
    return status

def place_point_deg_min(lat_deg_min: str, lon_deg_min: str, point_size: int = 5, point_color: str = "red"):
    """
    Place un point sur la carte à partir des coordonnées lat/lon (format "36°30") et affiche l'image.
    """
    # Paramètres codés en dur
    IMAGE_PATH = "carte/carte_trois_bleu_tunisie.PNG"  # Ajuste ce chemin si nécessaire
    ZONE_COLORS = {
        "nord": (23, 0, 220),    # #1700dc
        "centre": (120, 105, 254),  # #7869fe
        "sud": (201, 195, 255),    # #c9c3ff
        "terre": (253, 251, 194)   # #fdfbc2
    }
    MARGIN_LEFT = 50
    MARGIN_RIGHT = 50
    MARGIN_TOP = 50
    MARGIN_BOTTOM = 50
    
    # Limites de la carte (basées sur l'exemple fourni)
    lon_min_map = deg_min_to_decimal(7, 0)
    lon_max_map = deg_min_to_decimal(15, 0)
    lat_min_map = deg_min_to_decimal(33, 0)
    lat_max_map = deg_min_to_decimal(39, 0)
    
    # Conversion des coordonnées
    lat_parts = lat_deg_min.split('°')
    lon_parts = lon_deg_min.split('°')
    
    lat_deg = int(lat_parts[0])
    lat_min = float(lat_parts[1]) if lat_parts[1] else 0
    lon_deg = int(lon_parts[0])
    lon_min = float(lon_parts[1]) if lon_parts[1] else 0
    
    latitude = deg_min_to_decimal(lat_deg, lat_min)
    longitude = deg_min_to_decimal(lon_deg, lon_min)
    
    # Traiter l'image
    image, zone_contours, masks = process_image(IMAGE_PATH, ZONE_COLORS)
    
    # Calculer l'échelle
    km_per_pixel = calculate_scale(image, (lat_min_map, lat_max_map), 
                                  (lon_min_map, lon_max_map), 
                                  MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, MARGIN_BOTTOM)
    
    # Convertir en pixels (Mercator pour visualisation)
    width, height = image.shape[1], image.shape[0]
    x, y = latlon_to_pixel_mercator(latitude, longitude, width, height, 
                                    lon_min_map, lon_max_map, lat_min_map, lat_max_map)
    
    # Vérifier la position
    status_message = check_location(image, x, y, ZONE_COLORS, zone_contours, masks, km_per_pixel)
    print(status_message)
    
    # Dessiner le point
    img = Image.open(IMAGE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(img)
    left = x - point_size
    top = y - point_size
    right = x + point_size
    bottom = y + point_size
    draw.ellipse([left, top, right, bottom], fill=point_color)
    
    # Afficher les informations
    print(f"\n📍 Point aux coordonnées: {lat_deg}°{lat_min:.1f}, {lon_deg}°{lon_min:.1f}")
    print(f"Équivalent décimal: {latitude:.6f}°, {longitude:.6f}°")
    print(f"Point placé aux coordonnées pixel: ({x}, {y})")
    
    # Afficher l'image
    img_np = np.array(img)
    plt.figure(figsize=(8, 8))
    plt.imshow(img_np)
    plt.axis('off')
    plt.show()
    
    return x, y

# Exemple d'utilisation
if __name__ == "__main__":
    x, y = place_point_deg_min("37°00", "10°00")