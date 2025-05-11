from PIL import Image, ImageDraw
import math
import cv2
import numpy as np
from typing import Tuple
import matplotlib.pyplot as plt

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
    tolerance = 80
    lower_bound = np.array([max(0, c - tolerance) for c in color])
    upper_bound = np.array([min(255, c + tolerance) for c in color])
    return cv2.inRange(image, lower_bound, upper_bound)

def process_image(image_path: str, zone_color: Tuple[int, int, int]) -> Tuple[np.ndarray, list]:
    """Traite l'image pour extraire la zone de la couleur spécifiée."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Erreur de chargement de l'image : {image_path}")
    
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_rgb = cv2.GaussianBlur(image_rgb, (5, 5), 0)
    
    # Créer un masque pour la zone
    zone_mask = create_color_mask(image_rgb, zone_color)
    kernel = np.ones((3, 3), np.uint8)
    zone_mask = cv2.morphologyEx(zone_mask, cv2.MORPH_CLOSE, kernel)
    
    # Extraire les contours
    contours, _ = cv2.findContours(zone_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    zone_contours = [c for c in contours if cv2.contourArea(c) > 100]
    print(f"Nombre de contours détectés pour la zone bleue : {len(zone_contours)}")
    
    return image, zone_contours

def latlon_to_pixel(lat: float, lon: float, image: np.ndarray, lat_range: tuple, lon_range: tuple, 
                    margin_left: int, margin_right: int, margin_top: int, margin_bottom: int) -> Tuple[int, int]:
    """Convertit lat/lon en coordonnées pixel (projection linéaire simplifiée)."""
    if not (lat_range[0] <= lat <= lat_range[1]) or not (lon_range[0] <= lon <= lon_range[1]):
        raise ValueError(f"Coordonnées hors des limites de la carte: lat={lat}, lon={lon}")
    
    height, width = image.shape[:2]
    effective_width = width - margin_left - margin_right
    effective_height = height - margin_top - margin_bottom
    
    lat_normalized = (lat - lat_range[0]) / (lat_range[1] - lat_range[0])
    lon_normalized = (lon - lon_range[0]) / (lon_range[1] - lon_range[0])
    
    x = margin_left + int(lon_normalized * effective_width)
    y = margin_top + int((1 - lat_normalized) * effective_height)
    
    x = max(0, min(x, width - 1))
    y = max(0, min(y, height - 1))
    
    return x, y

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

def is_point_near_border(x: int, y: int, contours: list, km_per_pixel: float, border_threshold: float = 0.5) -> Tuple[bool, str]:
    """Vérifie si le point est proche de la frontière de la zone (en km)."""
    border_warning = ""
    near_border = False
    
    if contours:
        min_distance = get_min_distance_to_contour(x, y, contours, km_per_pixel)
        if min_distance <= border_threshold:
            near_border = True
            border_warning += (
                f"⚠️ ATTENTION : Le bateau est à {min_distance:.2f} km de la frontière de la zone interdite pour la pêche au feu. "
                "Risque d'entrée imminente dans une zone réglementée ! "
                "Veuillez ajuster votre trajectoire pour éviter la zone interdite."
            )
    
    return near_border, border_warning

def is_point_in_zone(x: int, y: int, contours: list) -> bool:
    """Vérifie si le point est dans la zone spécifiée."""
    point = (x, y)
    for contour in contours:
        if cv2.pointPolygonTest(contour, point, False) >= 0:
            return True
    return False

def check_location(lat: float, lon: float, x: int, y: int, contours: list, km_per_pixel: float) -> str:
    """Vérifie la position du bateau et génère des alertes."""
    in_zone = is_point_in_zone(x, y, contours)
    near_border, border_warning = is_point_near_border(x, y, contours, km_per_pixel)

    if in_zone:
        status = (
            "🚨 ALERTE : Le bateau est dans une zone INTERDITE pour la pêche au feu dans le Golfe de Tunis (zone bleue). "
            "Ceci constitue une violation des réglementations de pêche. "
            "Veuillez immédiatement repositionner votre bateau hors de la zone interdite."
        )
    else:
        status = (
            "✅ Le bateau est actuellement dans une zone autorisée pour la pêche au feu dans le Golfe de Tunis (hors zone bleue). "
            "Poursuivez vos activités en toute conformité avec la réglementation en vigueur."
        )

    if near_border:
        status += f"\n{border_warning}"

    return status

def place_point_deg_min(lat_deg_min: str, lon_deg_min: str, point_size: int = 5, point_color: str = "red"):
    """
    Place un point sur la carte à partir des coordonnées lat/lon (format "36°30") et affiche l'image.
    """
    # Paramètres codés en dur
    IMAGE_PATH = "carte/carte_tunisie_bleu_foncee.PNG"
    ZONE_COLOR = (0, 128, 255)  # Bleu (approximation RGB pour les zones interdites)
    MARGIN_LEFT = 50
    MARGIN_RIGHT = 50
    MARGIN_TOP = 50
    MARGIN_BOTTOM = 50
    
    # Limites de la carte (basées sur l'exemple fourni)
    lon_min_map = deg_min_to_decimal(7, 0)
    lon_max_map = deg_min_to_decimal(13, 0)
    lat_min_map = deg_min_to_decimal(33, 0)
    lat_max_map = deg_min_to_decimal(37, 43)
    
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
    image, zone_contours = process_image(IMAGE_PATH, ZONE_COLOR)
    
    # Calculer l'échelle
    km_per_pixel = calculate_scale(image, (lat_min_map, lat_max_map), 
                                  (lon_min_map, lon_max_map), 
                                  MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, MARGIN_BOTTOM)
    
    # Convertir en pixels (Mercator pour visualisation)
    width, height = image.shape[1], image.shape[0]
    x, y = latlon_to_pixel_mercator(latitude, longitude, width, height, 
                                    lon_min_map, lon_max_map, lat_min_map, lat_max_map)
    
    # Vérifier la position
    status_message = check_location(latitude, longitude, x, y, zone_contours, km_per_pixel)
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
    x, y = place_point_deg_min("37° 30", "8° 56")