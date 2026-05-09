"""
Map Generator Module
Generate HTML/Leaflet visualization from TDOA results
Translate create_html_file_osm.m ke Python
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from loguru import logger


class MapGenerator:
    """
    Generate interactive HTML maps using Leaflet.js
    Shows: RX positions, hyperbolas, heatmap, estimated TX location
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize map generator
        
        Args:
            output_dir: Directory to save HTML files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"MapGenerator initialized, output dir: {self.output_dir}")
    
    def generate_heatmap(self, 
                        doa_meters12: float,
                        doa_meters13: float,
                        doa_meters23: float,
                        rx1_lat: float, rx1_lon: float,
                        rx2_lat: float, rx2_lon: float,
                        rx3_lat: float, rx3_lon: float,
                        geo_ref_lat: float, geo_ref_lon: float,
                        resolution: int = 200) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate heatmap grid based on MSE (Mean Squared Error)
        Mimics create_heatmap.m dari MATLAB
        
        Parameters:
        -----------
        doa_meters12, doa_meters13, doa_meters23 : float
            TDOA measurements antara RX pairs (meters)
        rx*_lat, rx*_lon : float
            Receiver coordinates
        geo_ref_lat, geo_ref_lon : float
            Geodetic reference point
        resolution : int
            Grid resolution (resolution x resolution points)
        
        Returns:
            Tuple of (heat_lat, heat_lon, heatmap_magnitude)
        """
        
        try:
            logger.info(f"Generating heatmap with resolution {resolution}x{resolution}...")
            
            # Define heatmap area (±0.03 degrees around geo_ref)
            lat_span = 0.03
            lon_span = 0.03
            
            start_lat = geo_ref_lat - lat_span
            stop_lat = geo_ref_lat + lat_span
            start_lon = geo_ref_lon - lon_span
            stop_lon = geo_ref_lon + lon_span
            
            # Create grid
            heat_lat = np.linspace(start_lat, stop_lat, resolution)
            heat_lon = np.linspace(start_lon, stop_lon, resolution)
            
            # Initialize MSE matrix
            mse_doa = np.zeros((resolution, resolution))
            
            logger.debug(f"Lat range: {start_lat:.6f} to {stop_lat:.6f}")
            logger.debug(f"Lon range: {start_lon:.6f} to {stop_lon:.6f}")
            
            # Calculate MSE for each grid point
            for lat_idx in range(resolution):
                if lat_idx % 50 == 0:
                    logger.debug(f"  Processing lat index {lat_idx}/{resolution}")
                
                for lon_idx in range(resolution):
                    # Current grid point
                    point_lat = heat_lat[lat_idx]
                    point_lon = heat_lon[lon_idx]
                    
                    # Distance from point to each RX
                    dist_to_rx1 = self._dist_latlong(
                        point_lat, point_lon,
                        rx1_lat, rx1_lon,
                        geo_ref_lat, geo_ref_lon
                    )
                    
                    dist_to_rx2 = self._dist_latlong(
                        point_lat, point_lon,
                        rx2_lat, rx2_lon,
                        geo_ref_lat, geo_ref_lon
                    )
                    
                    dist_to_rx3 = self._dist_latlong(
                        point_lat, point_lon,
                        rx3_lat, rx3_lon,
                        geo_ref_lat, geo_ref_lon
                    )
                    
                    # Theoretical TDOA at this point
                    current_doa12 = dist_to_rx1 - dist_to_rx2
                    current_doa13 = dist_to_rx1 - dist_to_rx3
                    current_doa23 = dist_to_rx2 - dist_to_rx3
                    
                    # MSE: sum of squared errors
                    doa_error = (
                        (current_doa12 - doa_meters12)**2 +
                        (current_doa13 - doa_meters13)**2 +
                        (current_doa23 - doa_meters23)**2
                    )
                    
                    mse_doa[lon_idx, lat_idx] = doa_error
            
            # Invert MSE (higher MSE → lower value, lower MSE → higher value)
            mse_doa = 1.0 / (mse_doa + 1e-10)
            
            # Normalize to 0..1 range
            max_mse = np.max(mse_doa)
            if max_mse > 0:
                mse_doa = mse_doa / max_mse
            
            logger.info(f"✓ Heatmap generated: {np.min(mse_doa):.6f} to {np.max(mse_doa):.6f}")
            
            return heat_lat, heat_lon, mse_doa
            
        except Exception as e:
            logger.error(f"Error generating heatmap: {str(e)}", exc_info=True)
            raise
    
    def create_osm_html(self,
                       filename: str,
                       rx_positions: Dict[str, Tuple[float, float]],
                       hyperbolas: Dict[str, Tuple[List[float], List[float]]],
                       heatmap_data: Dict,
                       heatmap_threshold: float = 0.7) -> bool:
        """
        Create HTML file with OpenStreetMap (Leaflet.js) visualization
        
        Parameters:
        -----------
        filename : str
            Output filename
        rx_positions : dict
            {'RX1': (lat, lon), 'RX2': (lat, lon), ...}
        hyperbolas : dict
            {'RX1_RX2': (lat_array, lon_array), ...}
        heatmap_data : dict
            {'lat': array, 'lon': array, 'mag': array}
        heatmap_threshold : float
            Only show heatmap points with magnitude > threshold
        
        Returns:
            True if successful
        """
        
        try:
            logger.info(f"Creating OSM HTML map: {filename}")
            
            # Get center point (mean of all RX positions)
            all_lats = [pos[0] for pos in rx_positions.values()]
            all_lons = [pos[1] for pos in rx_positions.values()]
            center_lat = np.mean(all_lats)
            center_lon = np.mean(all_lons)
            
            # Start HTML document
            html_lines = [
                '<!DOCTYPE html>',
                '<html>',
                '<head>',
                '<title>TDOA Localization Map</title>',
                '<meta charset="utf-8" />',
                '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"',
                '      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="',
                '      crossorigin="" />',
                '<style>',
                '  body { font-family: Arial, sans-serif; }',
                '  #map { height: 100vh; }',
                '  .info { padding: 6px 8px; background: white; border-radius: 5px; }',
                '</style>',
                '</head>',
                '<body>',
                '<div id="map"></div>',
                '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"',
                '        integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="',
                '        crossorigin=""></script>',
                '<script src="leaflet-heat.js"></script>',
                '<script>'
            ]
            
            # Initialize map
            html_lines.extend([
                f'  var map = L.map("map").setView([{center_lat}, {center_lon}], 13);',
                '  L.tileLayer("http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {',
                '    attribution: "Map data &copy; OpenStreetMap contributors",',
                '    maxZoom: 18',
                '  }).addTo(map);',
                '  L.control.scale().addTo(map);'
            ])
            
            # Add RX markers
            logger.debug("Adding RX markers...")
            rx_colors = {
                'RX1': '#3388ff',  # Blue
                'RX2': '#33ff88',  # Green
                'RX3': '#ff8833',  # Orange
            }
            
            for rx_name, (lat, lon) in rx_positions.items():
                if 'TX' in rx_name or 'center' in rx_name.lower() or 'AVG' in rx_name:
                    color = '#ff0000'  # Red for TX/center points
                    radius = 8
                else:
                    color = rx_colors.get(rx_name, '#3388ff')
                    radius = 6
                
                html_lines.extend([
                    f'  L.circleMarker([{lat}, {lon}], {{',
                    f'    radius: {radius},',
                    f'    fillColor: "{color}",',
                    f'    color: "#000",',
                    f'    weight: 2,',
                    f'    opacity: 1,',
                    f'    fillOpacity: 0.8',
                    f'  }}).bindPopup("{rx_name}<br>Lat: {lat:.6f}<br>Lon: {lon:.6f}")',
                    f'   .addTo(map);'
                ])
            
            # Add hyperbolas
            logger.debug("Adding hyperbola curves...")
            hyp_colors = ['#0000FF', '#00FF00', '#FF0000']
            hyp_names = ['RX1-RX2', 'RX1-RX3', 'RX2-RX3']
            
            for idx, (hyp_name, (hyp_lats, hyp_lons)) in enumerate(hyperbolas.items()):
                color = hyp_colors[idx % len(hyp_colors)]
                name = hyp_names[idx % len(hyp_names)]
                
                # Build polyline coordinates
                coords_str = '['
                for lat, lon in zip(hyp_lats, hyp_lons):
                    coords_str += f'[{lat}, {lon}],'
                coords_str = coords_str.rstrip(',') + ']'
                
                html_lines.extend([
                    f'  L.polyline({coords_str}, {{',
                    f'    color: "{color}",',
                    f'    weight: 1,',
                    f'    opacity: 0.6',
                    f'  }}).addTo(map);'
                ])
            
            # Add heatmap
            logger.debug("Adding heatmap...")
            heat_data = heatmap_data.get('mag', np.array([]))
            heat_lats = heatmap_data.get('lat', np.array([]))
            heat_lons = heatmap_data.get('lon', np.array([]))
            
            heatmap_points = '['
            max_heat_mag = 0
            max_heat_lat = 0
            max_heat_lon = 0
            
            if len(heat_lats) > 0 and len(heat_lons) > 0:
                for lat_idx in range(len(heat_lats)):
                    for lon_idx in range(len(heat_lons)):
                        mag = heat_data[lon_idx, lat_idx] if lon_idx < heat_data.shape[1] else 0
                        
                        if mag > max_heat_mag:
                            max_heat_mag = mag
                            max_heat_lat = heat_lats[lat_idx]
                            max_heat_lon = heat_lons[lon_idx]
                        
                        if mag > heatmap_threshold:
                            heatmap_points += f'[{heat_lats[lat_idx]}, {heat_lons[lon_idx]}, {mag}],'
                
                heatmap_points = heatmap_points.rstrip(',') + ']'
            else:
                heatmap_points += ']'
            
            html_lines.extend([
                f'  L.heatLayer({heatmap_points}, {{',
                f'    radius: 15,',
                f'    blur: 15,',
                f'    maxZoom: 1',
                f'  }}).addTo(map);'
            ])
            
            # Mark maximum heat point (estimated TX location)
            if max_heat_mag > 0:
                html_lines.extend([
                    f'  L.circleMarker([{max_heat_lat}, {max_heat_lon}], {{',
                    f'    radius: 10,',
                    f'    fillColor: "#00FF00",',
                    f'    color: "#000",',
                    f'    weight: 2,',
                    f'    opacity: 1,',
                    f'    fillOpacity: 0.8',
                    f'  }}).bindPopup("Estimated TX<br>Lat: {max_heat_lat:.6f}<br>Lon: {max_heat_lon:.6f}<br>Confidence: {max_heat_mag*100:.1f}%")',
                    f'   .addTo(map);'
                ])
            
            # Close HTML
            html_lines.extend([
                '  </script>',
                '</body>',
                '</html>'
            ])
            
            # Write to file
            output_path = self.output_dir / filename
            with open(output_path, 'w') as f:
                f.write('\n'.join(html_lines))
            
            logger.info(f"✓ HTML map saved: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating HTML map: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def _latlong_to_xy(lat: float, lon: float,
                      ref_lat: float, ref_lon: float) -> Tuple[float, float]:
        """Convert lat/lon to XY (km)"""
        earth_circumf = 40074  # km
        y = (lat - ref_lat) / 360 * earth_circumf
        x = (lon - ref_lon) / 360 * np.cos(np.radians(ref_lat)) * earth_circumf
        return x, y
    
    @staticmethod
    def _dist_latlong(lat1: float, lon1: float,
                     lat2: float, lon2: float,
                     ref_lat: float, ref_lon: float) -> float:
        """Calculate distance between two lat/lon points (meters)"""
        x1, y1 = MapGenerator._latlong_to_xy(lat1, lon1, ref_lat, ref_lon)
        x2, y2 = MapGenerator._latlong_to_xy(lat2, lon2, ref_lat, ref_lon)
        return 1000 * np.sqrt((x1 - x2)**2 + (y1 - y2)**2)