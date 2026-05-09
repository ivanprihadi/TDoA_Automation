"""
Geometric calculations untuk TDOA
Generate hyperbola curves dan estimate TX location
"""

import numpy as np
from loguru import logger
from typing import Tuple, List, Dict

class GeometryEngine:
    """
    Konversi lat/long ke Cartesian dan generate hyperbolas
    Semua functions dari MATLAB: latlong2xy, xy2latlong, dist_latlong, gen_hyperbola, wrap2pi
    """
    
    EARTH_CIRCUMFERENCE = 40074  # km
    LIGHT_SPEED = 3e8  # m/s
    
    @staticmethod
    def latlong2xy(lat: float, lon: float, 
                  ref_lat: float, ref_lon: float) -> Tuple[float, float]:
        """
        Convert lat/long ke Cartesian XY (km)
        Menggunakan plane approximation around reference point
        
        Parameters:
        -----------
        lat, lon : float
            Latitude, Longitude (degrees)
        ref_lat, ref_lon : float
            Reference point untuk approximation
        
        Returns:
            (x, y) dalam km
        
        Dari MATLAB: latlong2xy.m
        """
        
        y = (lat - ref_lat) / 360 * GeometryEngine.EARTH_CIRCUMFERENCE
        x = ((lon - ref_lon) / 360 * 
             np.cos(np.radians(ref_lat)) * 
             GeometryEngine.EARTH_CIRCUMFERENCE)
        
        return x, y
    
    @staticmethod
    def xy2latlong(x: float, y: float,
                  ref_lat: float, ref_lon: float) -> Tuple[float, float]:
        """
        Convert Cartesian XY (km) ke lat/long
        
        Dari MATLAB: xy2latlong.m
        """
        
        lat = (y * 360 / GeometryEngine.EARTH_CIRCUMFERENCE) + ref_lat
        lon = ((x * 360) / (GeometryEngine.EARTH_CIRCUMFERENCE * 
                            np.cos(np.radians(ref_lat)))) + ref_lon
        
        return lat, lon
    
    @staticmethod
    def dist_latlong(lat1: float, lon1: float,
                    lat2: float, lon2: float,
                    ref_lat: float, ref_lon: float) -> float:
        """
        Calculate distance antara 2 lat/long points (meters)
        
        Dari MATLAB: dist_latlong.m
        """
        
        x1, y1 = GeometryEngine.latlong2xy(lat1, lon1, ref_lat, ref_lon)
        x2, y2 = GeometryEngine.latlong2xy(lat2, lon2, ref_lat, ref_lon)
        
        dist = 1000 * np.sqrt((x1 - x2)**2 + (y1 - y2)**2)  # Convert km to m
        
        return dist
    
    @staticmethod
    def wrap2pi(angle: float) -> float:
        """
        Wrap angle ke range -π to +π
        
        Dari MATLAB: wrap2pi.m
        """
        
        wrapped = angle
        
        while wrapped > np.pi:
            wrapped = -np.pi + (wrapped - np.pi)
        
        while wrapped < -np.pi:
            wrapped = np.pi + (wrapped + np.pi)
        
        return wrapped
    
    @staticmethod
    def generate_hyperbola(doa_meters: float,
                          rx1_lat: float, rx1_lon: float,
                          rx2_lat: float, rx2_lon: float,
                          geo_ref_lat: float, geo_ref_lon: float,
                          rx1_name: str = 'RX1',
                          rx2_name: str = 'RX2') -> Tuple[List[float], List[float]]:
        """
        Generate points pada hyperbola curve berdasarkan TDOA
        
        Parameters:
        -----------
        doa_meters : float
            Time difference of arrival (meters)
            Positive: RX1 menerima lebih dulu dari RX2
        rx1_lat, rx1_lon : float
            Position RX1
        rx2_lat, rx2_lon : float
            Position RX2
        geo_ref_lat, geo_ref_lon : float
            Geodetic reference point
        
        Returns:
            (points_lat, points_lon) - arrays of hyperbola points
        
        Dari MATLAB: gen_hyperbola.m
        Hyperbola definition: |r1 - r2| = doa_meters
        """
        
        try:
            logger.info(f"Generating hyperbola for {rx1_name}-{rx2_name}...")
            
            # Convert to XY coordinates
            rx1_x, rx1_y = GeometryEngine.latlong2xy(rx1_lat, rx1_lon, geo_ref_lat, geo_ref_lon)
            rx2_x, rx2_y = GeometryEngine.latlong2xy(rx2_lat, rx2_lon, geo_ref_lat, geo_ref_lon)
            
            # Distance between RX1 dan RX2
            rx_x_dist = rx2_x - rx1_x
            rx_y_dist = rx2_y - rx1_y
            
            rx_dist_complex = rx_x_dist + 1j * rx_y_dist
            dist_12_km = np.abs(rx_dist_complex)
            angle_12 = np.angle(rx_dist_complex)  # -π to +π
            
            logger.debug(f"  RX distance: {dist_12_km:.3f} km, angle: {np.degrees(angle_12):.1f}°")
            
            doa_km = doa_meters / 1000
            
            # Check validity
            if abs(doa_km) > dist_12_km:
                logger.warning(f"TDOA {doa_meters}m > RX distance {dist_12_km*1000}m")
                logger.warning("Correcting to 0.995 * RX distance (maximum possible)")
                doa_km = np.sign(doa_km) * 0.995 * dist_12_km
            
            # Generate hyperbola points using triangle inequality
            hyp_x_leg1 = []
            hyp_y_leg1 = []
            hyp_x_leg2 = []
            hyp_y_leg2 = []
            
            # Iterate over possible r1 distances (0 to 10 km in 50m steps)
            for r1 in np.arange(0, 10, 0.05):
                r2 = r1 - doa_km  # From hyperbola definition
                
                # Check triangle inequality: r1 + r2 > dist_12
                if (r2 + r1) > dist_12_km:
                    
                    # Cosine theorem: cos(C) = (a² + b² - c²) / (2ab)
                    acos_arg = (r2**2 - r1**2 - dist_12_km**2) / (-2 * r1 * dist_12_km)
                    
                    # Check if valid (must be -1 to +1 for arccos)
                    if -1 <= acos_arg <= 1:
                        hyp_angle = np.arccos(acos_arg)
                        
                        # Two branches of hyperbola
                        abs_angle1 = GeometryEngine.wrap2pi(angle_12 + hyp_angle)
                        x1 = rx1_x + r1 * np.cos(abs_angle1)
                        y1 = rx1_y + r1 * np.sin(abs_angle1)
                        hyp_x_leg1.append(x1)
                        hyp_y_leg1.append(y1)
                        
                        abs_angle2 = GeometryEngine.wrap2pi(angle_12 - hyp_angle)
                        x2 = rx1_x + r1 * np.cos(abs_angle2)
                        y2 = rx1_y + r1 * np.sin(abs_angle2)
                        hyp_x_leg2.append(x2)
                        hyp_y_leg2.append(y2)
            
            if len(hyp_x_leg1) == 0:
                logger.error("Could not construct hyperbola")
                return [], []
            
            # Combine both legs (flip leg1 untuk kontinuitas)
            hyp_x = np.concatenate([np.flipud(hyp_x_leg1), hyp_x_leg2])
            hyp_y = np.concatenate([np.flipud(hyp_y_leg1), hyp_y_leg2])
            
            # Convert back to lat/long
            points_lat = []
            points_lon = []
            
            for x, y in zip(hyp_x, hyp_y):
                lat, lon = GeometryEngine.xy2latlong(x, y, geo_ref_lat, geo_ref_lon)
                points_lat.append(lat)
                points_lon.append(lon)
            
            logger.info(f"✓ Generated {len(points_lat)} hyperbola points")
            
            return points_lat, points_lon
            
        except Exception as e:
            logger.error(f"✗ Hyperbola generation failed: {str(e)}")
            raise
    
    @staticmethod
    def find_intersection_point(hyp1_lat: List[float], hyp1_lon: List[float],
                               hyp2_lat: List[float], hyp2_lon: List[float],
                               geo_ref_lat: float, geo_ref_lon: float) -> Tuple[float, float]:
        """
        Find intersection point antara 2 hyperbolas
        Dengan mencari closest pair of points
        
        Returns:
            (avg_lat, avg_lon) - averaged intersection point
        
        Dari MATLAB: evaluation_main line 245-256
        """
        
        try:
            min_dist = float('inf')
            best_i, best_j = 0, 0
            
            # Find closest pair
            for i in range(len(hyp1_lat)):
                for j in range(len(hyp2_lat)):
                    dist = GeometryEngine.dist_latlong(
                        hyp1_lat[i], hyp1_lon[i],
                        hyp2_lat[j], hyp2_lon[j],
                        geo_ref_lat, geo_ref_lon
                    )
                    
                    if dist < min_dist:
                        min_dist = dist
                        best_i, best_j = i, j
            
            # Average the two closest points
            avg_lat = (hyp1_lat[best_i] + hyp2_lat[best_j]) / 2
            avg_lon = (hyp1_lon[best_i] + hyp2_lon[best_j]) / 2
            
            logger.debug(f"Intersection distance: {min_dist:.1f}m")
            
            return avg_lat, avg_lon
            
        except Exception as e:
            logger.error(f"✗ Intersection finding failed: {str(e)}")
            raise
    
    @staticmethod
    def find_tx_location_from_3_hyperbolas(
        hyp12_lat: List[float], hyp12_lon: List[float],
        hyp13_lat: List[float], hyp13_lon: List[float],
        hyp23_lat: List[float], hyp23_lon: List[float],
        geo_ref_lat: float, geo_ref_lon: float) -> Tuple[float, float]:
        """
        Find final TX location dari 3 hyperbolas
        Average the 3 intersection points
        
        Dari MATLAB: evaluation_main line 257-267
        """
        
        try:
            logger.info("Finding TX location from 3 hyperbola intersections...")
            
            # Find intersection for each pair
            lat12, lon12 = GeometryEngine.find_intersection_point(
                hyp12_lat, hyp12_lon,
                hyp13_lat, hyp13_lon,
                geo_ref_lat, geo_ref_lon
            )
            logger.debug(f"  Intersection 1-2/1-3: ({lat12:.8f}, {lon12:.8f})")
            
            lat13, lon13 = GeometryEngine.find_intersection_point(
                hyp12_lat, hyp12_lon,
                hyp23_lat, hyp23_lon,
                geo_ref_lat, geo_ref_lon
            )
            logger.debug(f"  Intersection 1-2/2-3: ({lat13:.8f}, {lon13:.8f})")
            
            lat23, lon23 = GeometryEngine.find_intersection_point(
                hyp13_lat, hyp13_lon,
                hyp23_lat, hyp23_lon,
                geo_ref_lat, geo_ref_lon
            )
            logger.debug(f"  Intersection 1-3/2-3: ({lat23:.8f}, {lon23:.8f})")
            
            # Average all 3 intersections
            avg_lat123 = (lat12 + lat13 + lat23) / 3
            avg_lon123 = (lon12 + lon13 + lon23) / 3
            
            logger.info(f"✓ Final TX location: ({avg_lat123:.8f}, {avg_lon123:.8f})")
            
            return avg_lat123, avg_lon123
            
        except Exception as e:
            logger.error(f"✗ TX location finding failed: {str(e)}")
            raise