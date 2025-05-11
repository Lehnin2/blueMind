from PIL import Image, ImageDraw
import math
import cv2
import numpy as np
from typing import Tuple
import matplotlib.pyplot as plt

# Convertisseurs entre degrés-minutes et décimal
def deg_min_to_decimal(deg: int, minutes: float) -> float:
    """Convertit des degrés et minutes en degrés décimaux"""
    return deg + minutes / 60

def decimal_to_deg_min(decimal_deg: float) -> tuple[int, float]:
    """Convertit des degrés décimaux en degrés et minutes"""
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

class NavigationZoneAnalyzer:
    def __init__(self, image_path: str, lat_range: tuple, lon_range: tuple):
        """Initialise l'analyseur pour détecter la zone orange (zone interdite)."""
        self.image_path = image_path
        self.lat_range = lat_range  # (lat_min, lat_max)
        self.lon_range = lon_range  # (lon_min, lon_max)
        self.restricted_zone_color = (255, 165, 0)  # Couleur orange RGB (zone interdite)
        self.image = None
        self.restricted_zone_mask = None
        self.restricted_zone_contours = None
        self.border_threshold = 20  # Distance en pixels pour l'alerte de proximité
        self.margin_left = 50
        self.margin_right = 50
        self.margin_top = 50
        self.margin_bottom = 50
        self.process_image()

    def process_image(self) -> None:
        """Traite l'image pour extraire la zone orange."""
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            raise ValueError(f"Erreur de chargement de l'image : {self.image_path}")
        
        image_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        image_rgb = cv2.GaussianBlur(image_rgb, (5, 5), 0)
        
        # Créer un masque pour la zone orange
        self.restricted_zone_mask = self.create_color_mask(image_rgb, self.restricted_zone_color)
        print("Masque créé, nombre de pixels orange détectés :", np.sum(self.restricted_zone_mask > 0))  # Debug
        kernel = np.ones((3, 3), np.uint8)
        self.restricted_zone_mask = cv2.morphologyEx(self.restricted_zone_mask, cv2.MORPH_CLOSE, kernel)
        
        # Extraire les contours de la zone orange
        contours, _ = cv2.findContours(self.restricted_zone_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.restricted_zone_contours = [c for c in contours if cv2.contourArea(c) > 50]  # Réduit à 50
        print(f"Nombre de contours détectés pour la zone interdite : {len(self.restricted_zone_contours)}")

    def create_color_mask(self, image: np.ndarray, color: Tuple[int, int, int]) -> np.ndarray:
        """Crée un masque pour une couleur donnée avec une tolérance."""
        tolerance = 100  # Augmenté pour plus de flexibilité
        lower_bound = np.array([max(0, c - tolerance) for c in color])
        upper_bound = np.array([min(255, c + tolerance) for c in color])
        return cv2.inRange(image, lower_bound, upper_bound)

    def latlon_to_pixel(self, lat: float, lon: float) -> Tuple[int, int]:
        """Convertit lat/lon en coordonnées pixel (projection linéaire simplifiée)."""
        if not (self.lat_range[0] <= lat <= self.lat_range[1]) or not (self.lon_range[0] <= lon <= self.lon_range[1]):
            raise ValueError(f"Coordonnées hors des limites de la carte: lat={lat}, lon={lon}")
        
        height, width = self.image.shape[:2]
        effective_width = width - self.margin_left - self.margin_right
        effective_height = height - self.margin_top - self.margin_bottom
        
        lat_normalized = (lat - self.lat_range[0]) / (self.lat_range[1] - self.lat_range[0])
        lon_normalized = (lon - self.lon_range[0]) / (self.lon_range[1] - self.lon_range[0])
        
        x = self.margin_left + int(lon_normalized * effective_width)
        y = self.margin_top + int((1 - lat_normalized) * effective_height)
        
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        
        return x, y

    def get_min_distance_to_contour(self, x: int, y: int) -> float:
        """Calcule la distance minimale entre un point et les contours de la zone orange."""
        min_distance = float('inf')
        point = np.array([x, y])
        for contour in self.restricted_zone_contours:
            for point_in_contour in contour:
                contour_point = point_in_contour[0]
                distance = np.linalg.norm(point - contour_point)
                min_distance = min(min_distance, distance)
        return min_distance

    def is_point_near_border(self, x: int, y: int) -> Tuple[bool, str]:
        """Vérifie si le point est proche de la frontière de la zone orange."""
        border_warning = ""
        near_border = False
        
        # Vérifier la proximité avec la frontière de la zone orange
        if self.restricted_zone_contours:
            min_distance = self.get_min_distance_to_contour(x, y)
            if min_distance <= self.border_threshold:
                near_border = True
                border_warning += (
                    f"⚠️ ATTENTION : Le bateau est à {min_distance:.2f} pixels de la frontière de la zone interdite à la navigation. "
                    "Risque d'entrée imminente dans une zone réglementée ! "
                    "Veuillez ajuster votre trajectoire pour éviter cette zone."
                )
        
        return near_border, border_warning

    def is_point_in_restricted_zone(self, x: int, y: int) -> bool:
        """Vérifie si le point est dans la zone orange (zone interdite)."""
        point = (x, y)
        for contour in self.restricted_zone_contours:
            if cv2.pointPolygonTest(contour, point, False) >= 0:
                return True
        return False

    def check_location(self, lat: float, lon: float, x: int, y: int) -> str:
        """Vérifie la position du bateau et génère des alertes."""
        in_zone = self.is_point_in_restricted_zone(x, y)
        near_border, border_warning = self.is_point_near_border(x, y)

        if in_zone:
            status = (
                "🚨 ALERTE CRITIQUE : Le bateau est DANS la zone interdite à la navigation pour les chalutiers dans le Golfe de Gabès ! "
                "Ceci constitue une violation grave des réglementations maritimes tunisiennes. "
                "Veuillez immédiatement quitter cette zone (zone orange sur la carte) pour éviter des sanctions."
            )
        else:
            status = (
                "✅ Le bateau est actuellement en dehors de la zone interdite à la navigation pour les chalutiers dans le Golfe de Gabès. "
                "Vous êtes en conformité avec les réglementations maritimes en vigueur. Continuez à naviguer prudemment."
            )

        if near_border:
            status += f"\n{border_warning}"

        return status

def place_point_deg_min(lat_deg_min: str, lon_deg_min: str, point_size: int = 5, point_color: str = "red"):
    """
    Place un point sur la carte à partir des coordonnées lat/lon (format "36°30") et affiche l'image sans sauvegarde.
    """
    # Chemin de l'image codé en dur
    IMAGE_PATH = "carte/carte_true_gulf_gabes.PNG"
    
    # Conversion des coordonnées
    lat_parts = lat_deg_min.split('°')
    lon_parts = lon_deg_min.split('°')
    
    lat_deg = int(lat_parts[0])
    lat_min = float(lat_parts[1]) if lat_parts[1] else 0
    
    lon_deg = int(lon_parts[0])
    lon_min = float(lon_parts[1]) if lon_parts[1] else 0
    
    # Convertir en degrés décimaux
    latitude = deg_min_to_decimal(lat_deg, lat_min)
    longitude = deg_min_to_decimal(lon_deg, lon_min)
    
    # Limites de la carte du golfe de Gabès (codées en dur)
    lon_min_map_deg = 10
    lon_min_map_min = 0
    lon_max_map_deg = 12
    lon_max_map_min = 0
    lat_min_map_deg = 33
    lat_min_map_min = 0
    lat_max_map_deg = 35
    lat_max_map_min = 0
    
    lon_min_map = deg_min_to_decimal(lon_min_map_deg, lon_min_map_min)
    lon_max_map = deg_min_to_decimal(lon_max_map_deg, lon_max_map_min)
    lat_min_map = deg_min_to_decimal(lat_min_map_deg, lat_min_map_min)
    lat_max_map = deg_min_to_decimal(lat_max_map_deg, lat_max_map_min)
    
    # Initialiser l'analyseur de zone
    analyzer = NavigationZoneAnalyzer(IMAGE_PATH, (lat_min_map, lat_max_map), (lon_min_map, lon_max_map))
    
    # Ouvre l'image
    img = Image.open(IMAGE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # Obtient les dimensions de l'image
    width, height = img.size
    
    # Convertit les coordonnées en pixels
    x, y = latlon_to_pixel_mercator(latitude, longitude, width, height, 
                                    lon_min_map, lon_max_map, lat_min_map, lat_max_map)
    
    # Vérifier la position et générer des alertes
    status_message = analyzer.check_location(latitude, longitude, x, y)
    print(status_message)
    
    # Dessine le point
    left = x - point_size
    top = y - point_size
    right = x + point_size
    bottom = y + point_size
    draw.ellipse([left, top, right, bottom], fill=point_color)
    
    # Affiche les informations
    print(f"\n📍 Point aux coordonnées: {lat_deg}°{lat_min:.1f}, {lon_deg}°{lon_min:.1f}")
    print(f"Équivalent décimal: {latitude:.6f}°, {longitude:.6f}°")
    print(f"Point placé aux coordonnées pixel: ({x}, {y})")
    
    # Convertir l'image PIL en tableau numpy pour l'afficher avec matplotlib
    img_np = np.array(img)
    
    # Afficher l'image
    plt.figure(figsize=(8, 8))
    plt.imshow(img_np)
    plt.axis('off')  # Masquer les axes
    plt.show()
    
    return x, y

# Exemple d'utilisation
if __name__ == "__main__":
    # Test avec des coordonnées
    x, y = place_point_deg_min(
        "34°00",  # Latitude
        "10°40"   # Longitude
    )