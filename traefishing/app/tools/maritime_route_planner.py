import numpy as np
import xarray as xr
import os
import heapq
import folium
from typing import List, Tuple, Dict, Optional

class MaritimeRoutePlanner:
    """
    Planificateur de route maritime utilisant l'algorithme A* pour trouver
    le chemin optimal entre deux points en tenant compte de la profondeur de l'eau
    et des obstacles terrestres.
    """
    
    def __init__(self, depth_file_path: str = None):
        """
        Initialise le planificateur de route maritime.
        
        Args:
            depth_file_path: Chemin vers le fichier netCDF contenant les données de profondeur
        """
        # Chemin par défaut vers le fichier de données de profondeur
        if depth_file_path is None:
            # Utiliser un chemin relatif au projet plutôt qu'un chemin absolu
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.depth_file_path = os.path.join(base_dir, "data", "carte_marine_tunisie.nc")
            # Vérifier si le fichier existe, sinon utiliser le chemin absolu comme fallback
            if not os.path.isfile(self.depth_file_path):
                self.depth_file_path = os.path.join("C:\\", "Users", "user", "OneDrive", "Bureau", 
                                           "multi-agent system", "data", "carte_marine_tunisie.nc")
        else:
            self.depth_file_path = depth_file_path
            
        # Charger les données de profondeur
        self.depth_data = self._load_depth_data()
        
        # Paramètres pour l'algorithme A*
        self.min_depth = 3.0  # Profondeur minimale en mètres pour la navigation
        self.grid_resolution = 0.05  # Résolution de la grille en degrés (réduite pour plus de précision)
        self.max_iterations = 20000  # Augmenté pour les longues distances
        self.segment_threshold = 300  # Distance en km au-delà de laquelle utiliser l'approche par segments
        self.segment_count = 5  # Nombre de segments pour les longues distances
        
    def _load_depth_data(self) -> Optional[xr.Dataset]:
        """
        Charge les données de profondeur à partir du fichier netCDF.
        
        Returns:
            Dataset xarray contenant les données de profondeur ou None en cas d'erreur
        """
        if not os.path.isfile(self.depth_file_path):
            print(f"Erreur: Fichier de profondeur non trouvé: {self.depth_file_path}")
            return None
            
        try:
            # Essayer d'abord avec le moteur par défaut
            return xr.open_dataset(self.depth_file_path)
        except Exception as e_default:
            try:
                # Essayer avec le moteur netCDF4
                print(f"⚠️ Moteur xarray par défaut a échoué ({e_default}), nouvel essai avec moteur netCDF4")
                return xr.open_dataset(self.depth_file_path, engine='netcdf4')
            except Exception as e_netcdf4:
                try:
                    # Essayer avec le moteur h5netcdf
                    print(f"⚠️ Moteur netCDF4 a échoué ({e_netcdf4}), nouvel essai avec moteur h5netcdf")
                    return xr.open_dataset(self.depth_file_path, engine='h5netcdf')
                except Exception as e_h5:
                    print(f"❌ Tous les moteurs xarray ont échoué ({e_h5})")
                    return None
    
    def get_depth_at_point(self, lat: float, lon: float) -> Optional[float]:
        """
        Obtient la profondeur à un point spécifique.
        
        Args:
            lat: Latitude du point
            lon: Longitude du point
            
        Returns:
            Profondeur en mètres ou None si les données ne sont pas disponibles
        """
        if self.depth_data is None:
            print(f"Avertissement: Données de profondeur non disponibles pour ({lat}, {lon})")
            return None
            
        try:
            # Vérifier si les coordonnées sont dans les limites des données
            lat_min = float(self.depth_data.lat.min())
            lat_max = float(self.depth_data.lat.max())
            lon_min = float(self.depth_data.lon.min())
            lon_max = float(self.depth_data.lon.max())
            
            if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
                print(f"Avertissement: Coordonnées ({lat}, {lon}) hors des limites des données ({lat_min}-{lat_max}, {lon_min}-{lon_max})")
                return None
                
            # Trouver les indices les plus proches dans le dataset
            point_data = self.depth_data.sel(lat=lat, lon=lon, method='nearest')
            
            # Vérifier si 'elevation' existe dans les données
            if 'elevation' not in point_data:
                print(f"Erreur: Variable 'elevation' non trouvée dans les données")
                return None
                
            # Utiliser 'elevation' au lieu de 'depth'
            elevation = float(point_data['elevation'].values)
            
            # Convertir l'élévation en profondeur (valeur négative = profondeur)
            return -elevation if elevation < 0 else 0
        except Exception as e:
            print(f"Erreur lors de l'obtention de la profondeur à ({lat}, {lon}): {e}")
            return None
    
    def is_navigable(self, lat: float, lon: float) -> bool:
        """
        Vérifie si un point est navigable (suffisamment profond et pas sur terre).
        
        Args:
            lat: Latitude du point
            lon: Longitude du point
            
        Returns:
            True si le point est navigable, False sinon
        """
        depth = self.get_depth_at_point(lat, lon)
        
        # Si la profondeur est None, considérer comme non navigable
        if depth is None:
            return False
            
        # Si la profondeur est trop faible, considérer comme non navigable
        # Note: get_depth_at_point retourne maintenant une valeur positive pour la profondeur
        return depth > self.min_depth
    
    def _get_neighbors(self, lat: float, lon: float) -> List[Tuple[float, float]]:
        """
        Obtient les points voisins dans les 8 directions en vérifiant qu'ils sont navigables.
        
        Args:
            lat: Latitude du point central
            lon: Longitude du point central
            
        Returns:
            Liste des coordonnées des points voisins navigables
        """
        neighbors = []
        for dlat in [-self.grid_resolution, 0, self.grid_resolution]:
            for dlon in [-self.grid_resolution, 0, self.grid_resolution]:
                if dlat == 0 and dlon == 0:
                    continue  # Ignorer le point central
                    
                new_lat = lat + dlat
                new_lon = lon + dlon
                
                # Vérifier si le point est dans les limites des données
                if self.depth_data is not None:
                    lat_min = float(self.depth_data.lat.min())
                    lat_max = float(self.depth_data.lat.max())
                    lon_min = float(self.depth_data.lon.min())
                    lon_max = float(self.depth_data.lon.max())
                    
                    if lat_min <= new_lat <= lat_max and lon_min <= new_lon <= lon_max:
                        # Vérifier si le point est navigable avant de l'ajouter
                        depth = self.get_depth_at_point(new_lat, new_lon)
                        if depth is not None and depth > self.min_depth:
                            neighbors.append((new_lat, new_lon))
                else:
                    # Si pas de données de profondeur, ajouter quand même le voisin
                    neighbors.append((new_lat, new_lon))
                    
        return neighbors
    
    def _heuristic(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcule l'heuristique (distance approximative) entre deux points.
        Utilise la distance euclidienne pour simplifier.
        
        Args:
            lat1, lon1: Coordonnées du premier point
            lat2, lon2: Coordonnées du deuxième point
            
        Returns:
            Distance approximative entre les points
        """
        # Conversion approximative des degrés en km
        lat_km = 111.0  # 1 degré de latitude ≈ 111 km
        lon_km = 111.0 * np.cos(np.radians((lat1 + lat2) / 2))  # Ajustement pour la longitude
        
        dlat = (lat2 - lat1) * lat_km
        dlon = (lon2 - lon1) * lon_km
        
        return np.sqrt(dlat**2 + dlon**2)
    
    def find_route(self, start_lat: float, start_lon: float, 
                   dest_lat: float, dest_lon: float) -> List[Dict[str, float]]:
        """
        Trouve une route optimale entre deux points en utilisant l'algorithme A*.
        Pour les longues distances, utilise une approche par segments.
        
        Args:
            start_lat, start_lon: Coordonnées du point de départ
            dest_lat, dest_lon: Coordonnées du point de destination
            
        Returns:
            Liste de points formant la route [{"lat": lat, "lon": lon}, ...]
        """
        if self.depth_data is None:
            print("Erreur: Données de profondeur non disponibles")
            # Retourner une ligne droite simple si pas de données de profondeur
            return self._straight_line_route(start_lat, start_lon, dest_lat, dest_lon)
        
        # Vérifier si les points de départ et d'arrivée sont navigables
        if not self.is_navigable(start_lat, start_lon):
            print("Avertissement: Point de départ non navigable")
            # Trouver un point navigable proche du départ
            start_lat, start_lon = self._find_nearest_navigable_point(start_lat, start_lon)
            print(f"Nouveau point de départ navigable: ({start_lat}, {start_lon})")
        
        if not self.is_navigable(dest_lat, dest_lon):
            print("Avertissement: Point de destination non navigable")
            # Trouver un point navigable proche de la destination
            dest_lat, dest_lon = self._find_nearest_navigable_point(dest_lat, dest_lon)
            print(f"Nouveau point de destination navigable: ({dest_lat}, {dest_lon})")
        
        # Calculer la distance approximative entre les points
        distance_km = self._heuristic(start_lat, start_lon, dest_lat, dest_lon)
        
        # Pour les longues distances, utiliser une approche par segments
        if distance_km > self.segment_threshold:
            print(f"Distance de {distance_km:.1f} km, utilisation de l'approche par segments")
            return self._find_route_by_segments(start_lat, start_lon, dest_lat, dest_lon)
        
        # Pour les distances plus courtes, utiliser l'algorithme A* standard
        return self._find_route_a_star(start_lat, start_lon, dest_lat, dest_lon)
    
    def _find_route_a_star(self, start_lat: float, start_lon: float, 
                          dest_lat: float, dest_lon: float) -> List[Dict[str, float]]:
        """
        Implémentation de l'algorithme A* pour trouver une route optimale.
        
        Args:
            start_lat, start_lon: Coordonnées du point de départ
            dest_lat, dest_lon: Coordonnées du point de destination
            
        Returns:
            Liste de points formant la route [{"lat": lat, "lon": lon}, ...]
        """
        # Initialiser les structures pour A*
        open_set = []
        closed_set = set()
        
        # Utiliser un tuple (heuristique + coût, coût, lat, lon) pour la file de priorité
        heapq.heappush(open_set, (0, 0, start_lat, start_lon))
        
        # Dictionnaire pour stocker le chemin parcouru
        came_from = {}
        
        # Coût du chemin du départ à chaque point
        g_score = {(start_lat, start_lon): 0}
        
        # Utiliser le nombre maximum d'itérations défini dans l'initialisation
        iterations = 0
        
        while open_set and iterations < self.max_iterations:
            iterations += 1
            
            # Obtenir le point avec le score f le plus bas
            _, current_g, current_lat, current_lon = heapq.heappop(open_set)
            current = (current_lat, current_lon)
            
            # Si nous avons atteint la destination (ou sommes suffisamment proches)
            if self._heuristic(current_lat, current_lon, dest_lat, dest_lon) < self.grid_resolution:
                # Reconstruire le chemin
                path = self._reconstruct_path(came_from, current, start_lat, start_lon)
                print(f"Route trouvée en {iterations} itérations")
                return path
            
            # Marquer comme visité
            closed_set.add(current)
            
            # Explorer les voisins
            for neighbor_lat, neighbor_lon in self._get_neighbors(current_lat, current_lon):
                neighbor = (neighbor_lat, neighbor_lon)
                
                # Ignorer si déjà visité
                if neighbor in closed_set:
                    continue
                
                # Vérifier si navigable
                if not self.is_navigable(neighbor_lat, neighbor_lon):
                    closed_set.add(neighbor)  # Marquer comme non navigable
                    continue
                
                # Calculer le nouveau score g (coût du chemin)
                # Coût diagonal = 1.414, coût orthogonal = 1
                is_diagonal = (neighbor_lat != current_lat) and (neighbor_lon != current_lon)
                move_cost = 1.414 if is_diagonal else 1.0
                
                # Ajuster le coût en fonction de la profondeur (pénaliser les eaux peu profondes)
                depth = self.get_depth_at_point(neighbor_lat, neighbor_lon)
                if depth is not None and depth < 20:  # Eau peu profonde
                    depth_factor = max(0.5, (depth - self.min_depth) / (20 - self.min_depth))
                    move_cost /= depth_factor  # Augmenter le coût pour les eaux peu profondes
                
                # Pénaliser fortement les points qui pourraient traverser la terre
                # en vérifiant les points intermédiaires entre le point actuel et le voisin
                if self._might_cross_land(current_lat, current_lon, neighbor_lat, neighbor_lon):
                    move_cost *= 10  # Pénalité importante pour éviter de traverser la terre
                
                tentative_g = g_score.get(current, float('inf')) + move_cost
                
                # Si nous avons trouvé un meilleur chemin vers ce voisin
                if tentative_g < g_score.get(neighbor, float('inf')):
                    # Mettre à jour le chemin
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    
                    # Calculer le score f (g + heuristique)
                    f_score = tentative_g + self._heuristic(neighbor_lat, neighbor_lon, dest_lat, dest_lon)
                    
                    # Ajouter à la file de priorité
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor_lat, neighbor_lon))
        
        print(f"Aucune route trouvée après {iterations} itérations")
        # Si aucune route n'est trouvée, retourner une ligne droite
        return self._straight_line_route(start_lat, start_lon, dest_lat, dest_lon)
    
    def _find_route_by_segments(self, start_lat: float, start_lon: float, 
                               dest_lat: float, dest_lon: float) -> List[Dict[str, float]]:
        """
        Trouve une route en divisant le trajet en segments plus courts.
        
        Args:
            start_lat, start_lon: Coordonnées du point de départ
            dest_lat, dest_lon: Coordonnées du point de destination
            
        Returns:
            Liste de points formant la route [{"lat": lat, "lon": lon}, ...]
        """
        # Créer des points intermédiaires en ligne droite
        waypoints = []
        for i in range(1, self.segment_count):
            fraction = i / self.segment_count
            lat = start_lat + fraction * (dest_lat - start_lat)
            lon = start_lon + fraction * (dest_lon - start_lon)
            
            # Trouver un point navigable proche du waypoint
            nav_lat, nav_lon = self._find_nearest_navigable_point(lat, lon)
            waypoints.append((nav_lat, nav_lon))
        
        # Ajouter le point de départ et d'arrivée
        all_points = [(start_lat, start_lon)] + waypoints + [(dest_lat, dest_lon)]
        
        # Trouver une route pour chaque segment
        complete_route = []
        for i in range(len(all_points) - 1):
            from_lat, from_lon = all_points[i]
            to_lat, to_lon = all_points[i + 1]
            
            print(f"Calcul du segment {i+1}/{len(all_points)-1}: ({from_lat}, {from_lon}) à ({to_lat}, {to_lon})")
            
            # Utiliser A* pour ce segment
            segment_route = self._find_route_a_star(from_lat, from_lon, to_lat, to_lon)
            
            # Ajouter les points du segment à la route complète (sauf le dernier pour éviter les doublons)
            if i < len(all_points) - 2:
                complete_route.extend(segment_route[:-1])
            else:
                complete_route.extend(segment_route)  # Inclure le dernier point pour le dernier segment
        
        return complete_route
    
    def _might_cross_land(self, lat1: float, lon1: float, lat2: float, lon2: float, checks: int = 3) -> bool:
        """
        Vérifie si une ligne droite entre deux points pourrait traverser la terre.
        
        Args:
            lat1, lon1: Coordonnées du premier point
            lat2, lon2: Coordonnées du deuxième point
            checks: Nombre de points intermédiaires à vérifier
            
        Returns:
            True si la ligne pourrait traverser la terre, False sinon
        """
        # Pour les points adjacents, pas besoin de vérifier
        if abs(lat1 - lat2) <= self.grid_resolution and abs(lon1 - lon2) <= self.grid_resolution:
            return False
        
        # Vérifier plusieurs points intermédiaires
        for i in range(1, checks + 1):
            fraction = i / (checks + 1)
            lat = lat1 + fraction * (lat2 - lat1)
            lon = lon1 + fraction * (lon2 - lon1)
            
            # Si un point intermédiaire n'est pas navigable, la ligne pourrait traverser la terre
            if not self.is_navigable(lat, lon):
                return True
        
        return False
    
    def _reconstruct_path(self, came_from: Dict, current: Tuple[float, float], 
                          start_lat: float, start_lon: float) -> List[Dict[str, float]]:
        """
        Reconstruit le chemin à partir du dictionnaire came_from.
        
        Args:
            came_from: Dictionnaire des points précédents
            current: Point final
            start_lat, start_lon: Coordonnées du point de départ
            
        Returns:
            Liste de points formant la route [{"lat": lat, "lon": lon}, ...]
        """
        path = []
        while current in came_from:
            lat, lon = current
            path.append({"lat": lat, "lon": lon})
            current = came_from[current]
        
        # Ajouter le point de départ
        path.append({"lat": start_lat, "lon": start_lon})
        
        # Inverser le chemin pour qu'il aille du départ à l'arrivée
        path.reverse()
        
        return path
    
    def _find_nearest_navigable_point(self, lat: float, lon: float, max_distance: float = 0.5) -> Tuple[float, float]:
        """
        Trouve le point navigable le plus proche d'un point donné.
        
        Args:
            lat, lon: Coordonnées du point de référence
            max_distance: Distance maximale de recherche en degrés
            
        Returns:
            Coordonnées du point navigable le plus proche
        """
        # Si le point est déjà navigable, le retourner directement
        if self.is_navigable(lat, lon):
            return lat, lon
            
        # Recherche en spirale pour trouver un point navigable
        best_distance = float('inf')
        best_point = (lat, lon)  # Par défaut, retourner le point original
        
        # Augmenter progressivement la distance de recherche
        for distance in [0.01, 0.02, 0.05, 0.1, 0.2, 0.3, max_distance]:
            # Nombre de points à vérifier autour du cercle
            num_points = max(8, int(distance * 100))
            
            for i in range(num_points):
                angle = 2 * np.pi * i / num_points
                new_lat = lat + distance * np.sin(angle)
                new_lon = lon + distance * np.cos(angle)
                
                # Vérifier si le point est dans les limites des données
                if self.depth_data is not None:
                    lat_min = float(self.depth_data.lat.min())
                    lat_max = float(self.depth_data.lat.max())
                    lon_min = float(self.depth_data.lon.min())
                    lon_max = float(self.depth_data.lon.max())
                    
                    if not (lat_min <= new_lat <= lat_max and lon_min <= new_lon <= lon_max):
                        continue
                
                # Vérifier si le point est navigable
                if self.is_navigable(new_lat, new_lon):
                    # Calculer la distance euclidienne
                    current_distance = self._heuristic(lat, lon, new_lat, new_lon)
                    
                    if current_distance < best_distance:
                        best_distance = current_distance
                        best_point = (new_lat, new_lon)
                        
                        # Si on trouve un point suffisamment proche, on s'arrête
                        if best_distance < 0.05:
                            return best_point[0], best_point[1]
        
        return best_point[0], best_point[1]
    
    def _straight_line_route(self, start_lat: float, start_lon: float, 
                            dest_lat: float, dest_lon: float, num_points: int = 10) -> List[Dict[str, float]]:
        """
        Crée une route en ligne droite entre deux points.
        
        Args:
            start_lat, start_lon: Coordonnées du point de départ
            dest_lat, dest_lon: Coordonnées du point de destination
            num_points: Nombre de points intermédiaires
            
        Returns:
            Liste de points formant la route [{"lat": lat, "lon": lon}, ...]
        """
        path = []
        for i in range(num_points + 1):
            fraction = i / num_points
            lat = start_lat + fraction * (dest_lat - start_lat)
            lon = start_lon + fraction * (dest_lon - start_lon)
            path.append({"lat": lat, "lon": lon})
        return path
    
    def create_route_map(self, route: List[Dict[str, float]], 
                        start_lat: float, start_lon: float,
                        dest_lat: float, dest_lon: float) -> folium.Map:
        """
        Crée une carte Folium avec la route.
        
        Args:
            route: Liste de points formant la route
            start_lat, start_lon: Coordonnées du point de départ
            dest_lat, dest_lon: Coordonnées du point de destination
            
        Returns:
            Carte Folium avec la route
        """
        # Calculer le centre de la carte
        center_lat = (start_lat + dest_lat) / 2
        center_lon = (start_lon + dest_lon) / 2
        
        # Créer la carte
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10, 
                      tiles='OpenStreetMap')
        
        # Ajouter des marqueurs pour le départ et l'arrivée
        folium.Marker(
            location=[start_lat, start_lon],
            popup='Départ',
            icon=folium.Icon(color='green', icon='play')
        ).add_to(m)
        
        folium.Marker(
            location=[dest_lat, dest_lon],
            popup='Destination',
            icon=folium.Icon(color='red', icon='stop')
        ).add_to(m)
        
        # Ajouter la ligne de la route
        points = [(point["lat"], point["lon"]) for point in route]
        folium.PolyLine(
            points,
            color='blue',
            weight=5,
            opacity=0.7
        ).add_to(m)
        
        # Ajouter des marqueurs pour les points intermédiaires
        for i, point in enumerate(route[1:-1], 1):
            folium.CircleMarker(
                location=[point["lat"], point["lon"]],
                radius=3,
                color='blue',
                fill=True,
                fill_color='blue',
                fill_opacity=0.7,
                popup=f'Point {i}'
            ).add_to(m)
        
        return m

# Exemple d'utilisation
if __name__ == "__main__":
    # Créer une instance du planificateur
    planner = MaritimeRoutePlanner()
    
    # Coordonnées d'exemple (Tunis à Sfax)
    start_lat, start_lon = 36.8, 10.2  # Tunis
    dest_lat, dest_lon = 34.7, 10.8    # Sfax
    
    print(f"Recherche d'une route de ({start_lat}, {start_lon}) à ({dest_lat}, {dest_lon})...")
    
    # Trouver la route
    route = planner.find_route(start_lat, start_lon, dest_lat, dest_lon)
    
    # Afficher la route
    print(f"Route trouvée avec {len(route)} points:")
    for i, point in enumerate(route):
        print(f"Point {i}: ({point['lat']}, {point['lon']})")
    
    # Créer et sauvegarder la carte
    map_file = "maritime_route.html"
    m = planner.create_route_map(route, start_lat, start_lon, dest_lat, dest_lon)
    m.save(map_file)
    
    print(f"Carte sauvegardée dans {map_file}")