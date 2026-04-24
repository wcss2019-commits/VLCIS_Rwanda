"""Early Warning System for VLCIS at 3km resolution.

Generates real-time alerts for:
- Flood Risk
- Drought Risk
- Heat Stress

At 3km grid resolution covering entire Rwanda (~60,000 VLCIS Stations).
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VLCISGridSystem:
    """3km resolution grid system for Rwanda."""
    
    def __init__(self):
        """Initialize 3km grid system for Rwanda.
        
        Rwanda bounds: 2.0°S to 2.8°S, 28.8°E to 30.9°E
        Grid resolution: 3km ≈ 0.027° at equator
        """
        self.lat_min, self.lat_max = -2.8, 2.0
        self.lon_min, self.lon_max = 28.8, 30.9
        self.cell_size_degrees = 0.027  # ~3km at equator
        
        self.grid_points = self._create_grid()
        logger.info(f"Created 3km grid with {len(self.grid_points)} stations")
    
    def _create_grid(self) -> pd.DataFrame:
        """Create regular 3km grid points across Rwanda.
        
        Returns:
            DataFrame with grid coordinates and VLCIS station IDs
        """
        lats = np.arange(self.lat_min, self.lat_max, self.cell_size_degrees)
        lons = np.arange(self.lon_min, self.lon_max, self.cell_size_degrees)
        
        grid_data = []
        station_id = 0
        
        for lat in lats:
            for lon in lons:
                # Check if point is approximately within Rwanda bounds
                if self._is_in_rwanda(lat, lon):
                    grid_data.append({
                        'vlcis_station_id': f'VLCIS_{station_id:06d}',
                        'latitude': lat,
                        'longitude': lon,
                        'grid_cell': f"{lat:.3f}_{lon:.3f}"
                    })
                    station_id += 1
        
        grid_df = pd.DataFrame(grid_data)
        logger.info(f"Created {len(grid_df)} grid cells covering Rwanda")
        return grid_df
    
    def _is_in_rwanda(self, lat: float, lon: float) -> bool:
        """Check if coordinate is approximately in Rwanda.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if approximately in Rwanda
        """
        # Simple bounding box check
        return (self.lat_min <= lat <= self.lat_max and 
                self.lon_min <= lon <= self.lon_max)


class EarlyWarningSystem:
    """Real-time early warning system for 3km grid."""
    
    # Risk thresholds and alert levels
    ALERT_LEVELS = {
        'NORMAL': {'value': 0, 'color': 'green'},
        'WATCH': {'value': 1, 'color': 'yellow'},
        'WARNING': {'value': 2, 'color': 'orange'},
        'DANGER': {'value': 3, 'color': 'red'}
    }
    
    FLOOD_THRESHOLDS = {
        'rainfall_24h_mm': [10, 30, 50],  # WATCH, WARNING, DANGER
        'soil_moisture_percent': [80, 85, 90],
        'cumulative_rain_7d': [100, 200, 350]
    }
    
    DROUGHT_THRESHOLDS = {
        'rainfall_30d_deficit_percent': [-20, -40, -60],  # WATCH, WARNING, DANGER
        'soil_moisture_percent': [30, 20, 10],
        'et0_ratio': [1.2, 1.5, 1.8]  # ET0/Rainfall ratio
    }
    
    HEAT_THRESHOLDS = {
        'wet_bulb_temperature_c': [26, 28, 30],  # WATCH, WARNING, DANGER
        'heat_index_c': [38, 41, 44]
    }
    
    def __init__(self):
        """Initialize EWS with grid system and thresholds."""
        self.grid = VLCISGridSystem()
        self.alerts_history = []
        
    def assess_flood_risk(
        self,
        station_data: Dict[str, float]
    ) -> Tuple[str, float, List[str]]:
        """Assess flood risk for a VLCIS station.
        
        Args:
            station_data: Dictionary with meteorological data
                - rainfall_24h_mm
                - soil_moisture_percent
                - cumulative_rain_7d
                
        Returns:
            Tuple of (alert_level, risk_score, recommendations)
        """
        risk_scores = []
        triggered_factors = []
        
        # 1. Rainfall intensity (24-hour)
        rainfall_24h = station_data.get('rainfall_24h_mm', 0)
        if rainfall_24h >= self.FLOOD_THRESHOLDS['rainfall_24h_mm'][2]:
            risk_scores.append(3)
            triggered_factors.append(f"Heavy rainfall: {rainfall_24h}mm in 24h")
        elif rainfall_24h >= self.FLOOD_THRESHOLDS['rainfall_24h_mm'][1]:
            risk_scores.append(2)
            triggered_factors.append(f"Moderate rainfall: {rainfall_24h}mm in 24h")
        elif rainfall_24h >= self.FLOOD_THRESHOLDS['rainfall_24h_mm'][0]:
            risk_scores.append(1)
            triggered_factors.append(f"Light rainfall: {rainfall_24h}mm in 24h")
        else:
            risk_scores.append(0)
        
        # 2. Soil saturation
        soil_moisture = station_data.get('soil_moisture_0_7cm_percent', 0)
        if soil_moisture >= self.FLOOD_THRESHOLDS['soil_moisture_percent'][2]:
            risk_scores.append(3)
            triggered_factors.append(f"High soil saturation: {soil_moisture}%")
        elif soil_moisture >= self.FLOOD_THRESHOLDS['soil_moisture_percent'][1]:
            risk_scores.append(2)
            triggered_factors.append(f"Moderate soil saturation: {soil_moisture}%")
        elif soil_moisture >= self.FLOOD_THRESHOLDS['soil_moisture_percent'][0]:
            risk_scores.append(1)
            triggered_factors.append(f"Elevated soil moisture: {soil_moisture}%")
        else:
            risk_scores.append(0)
        
        # 3. Cumulative 7-day rainfall
        cum_rain_7d = station_data.get('cumulative_rain_7d_mm', 0)
        if cum_rain_7d >= self.FLOOD_THRESHOLDS['cumulative_rain_7d'][2]:
            risk_scores.append(3)
            triggered_factors.append(f"Very high 7-day rain: {cum_rain_7d}mm")
        elif cum_rain_7d >= self.FLOOD_THRESHOLDS['cumulative_rain_7d'][1]:
            risk_scores.append(2)
            triggered_factors.append(f"High 7-day rain: {cum_rain_7d}mm")
        elif cum_rain_7d >= self.FLOOD_THRESHOLDS['cumulative_rain_7d'][0]:
            risk_scores.append(1)
            triggered_factors.append(f"Elevated 7-day rain: {cum_rain_7d}mm")
        else:
            risk_scores.append(0)
        
        # Maximum risk score determines alert level
        max_score = max(risk_scores) if risk_scores else 0
        alert_level = self._score_to_alert_level(max_score)
        
        # Risk score 0-1
        risk_score = max_score / 3.0
        
        # Recommendations
        recommendations = self._get_flood_recommendations(max_score)
        
        return alert_level, risk_score, triggered_factors + recommendations
    
    def assess_drought_risk(
        self,
        station_data: Dict[str, float]
    ) -> Tuple[str, float, List[str]]:
        """Assess drought risk for a VLCIS station.
        
        Args:
            station_data: Dictionary with meteorological data
                - rainfall_30d_deficit_percent
                - soil_moisture_percent
                - et0_ratio
                
        Returns:
            Tuple of (alert_level, risk_score, recommendations)
        """
        risk_scores = []
        triggered_factors = []
        
        # 1. Rainfall deficit
        rain_deficit = station_data.get('rainfall_30d_deficit_percent', 0)
        if rain_deficit <= self.DROUGHT_THRESHOLDS['rainfall_30d_deficit_percent'][2]:
            risk_scores.append(3)
            triggered_factors.append(f"Severe rainfall deficit: {rain_deficit}%")
        elif rain_deficit <= self.DROUGHT_THRESHOLDS['rainfall_30d_deficit_percent'][1]:
            risk_scores.append(2)
            triggered_factors.append(f"High rainfall deficit: {rain_deficit}%")
        elif rain_deficit <= self.DROUGHT_THRESHOLDS['rainfall_30d_deficit_percent'][0]:
            risk_scores.append(1)
            triggered_factors.append(f"Moderate rainfall deficit: {rain_deficit}%")
        else:
            risk_scores.append(0)
        
        # 2. Soil moisture depletion
        soil_moisture = station_data.get('soil_moisture_0_7cm_percent', 50)
        if soil_moisture <= self.DROUGHT_THRESHOLDS['soil_moisture_percent'][2]:
            risk_scores.append(3)
            triggered_factors.append(f"Critical soil moisture: {soil_moisture}%")
        elif soil_moisture <= self.DROUGHT_THRESHOLDS['soil_moisture_percent'][1]:
            risk_scores.append(2)
            triggered_factors.append(f"Low soil moisture: {soil_moisture}%")
        elif soil_moisture <= self.DROUGHT_THRESHOLDS['soil_moisture_percent'][0]:
            risk_scores.append(1)
            triggered_factors.append(f"Declining soil moisture: {soil_moisture}%")
        else:
            risk_scores.append(0)
        
        # 3. ET0/Rainfall ratio (evaporative demand vs supply)
        et0_ratio = station_data.get('et0_ratio', 0)
        if et0_ratio >= self.DROUGHT_THRESHOLDS['et0_ratio'][2]:
            risk_scores.append(3)
            triggered_factors.append(f"Extreme ET0/rain ratio: {et0_ratio:.2f}")
        elif et0_ratio >= self.DROUGHT_THRESHOLDS['et0_ratio'][1]:
            risk_scores.append(2)
            triggered_factors.append(f"High ET0/rain ratio: {et0_ratio:.2f}")
        elif et0_ratio >= self.DROUGHT_THRESHOLDS['et0_ratio'][0]:
            risk_scores.append(1)
            triggered_factors.append(f"Elevated ET0/rain ratio: {et0_ratio:.2f}")
        else:
            risk_scores.append(0)
        
        max_score = max(risk_scores) if risk_scores else 0
        alert_level = self._score_to_alert_level(max_score)
        risk_score = max_score / 3.0
        recommendations = self._get_drought_recommendations(max_score)
        
        return alert_level, risk_score, triggered_factors + recommendations
    
    def assess_heat_stress_risk(
        self,
        station_data: Dict[str, float]
    ) -> Tuple[str, float, List[str]]:
        """Assess heat stress risk for a VLCIS station.
        
        Args:
            station_data: Dictionary with meteorological data
                - wet_bulb_temperature_c
                - heat_index_c
                
        Returns:
            Tuple of (alert_level, risk_score, recommendations)
        """
        risk_scores = []
        triggered_factors = []
        
        # 1. Wet-bulb temperature (best indicator of heat stress)
        wet_bulb = station_data.get('wet_bulb_temperature_c', 0)
        if wet_bulb >= self.HEAT_THRESHOLDS['wet_bulb_temperature_c'][2]:
            risk_scores.append(3)
            triggered_factors.append(f"Extreme heat stress: WB={wet_bulb:.1f}°C")
        elif wet_bulb >= self.HEAT_THRESHOLDS['wet_bulb_temperature_c'][1]:
            risk_scores.append(2)
            triggered_factors.append(f"High heat stress: WB={wet_bulb:.1f}°C")
        elif wet_bulb >= self.HEAT_THRESHOLDS['wet_bulb_temperature_c'][0]:
            risk_scores.append(1)
            triggered_factors.append(f"Moderate heat stress: WB={wet_bulb:.1f}°C")
        else:
            risk_scores.append(0)
        
        # 2. Heat index
        heat_index = station_data.get('heat_index_c', 0)
        if heat_index >= self.HEAT_THRESHOLDS['heat_index_c'][2]:
            risk_scores.append(3)
            triggered_factors.append(f"Extreme heat index: {heat_index:.1f}°C")
        elif heat_index >= self.HEAT_THRESHOLDS['heat_index_c'][1]:
            risk_scores.append(2)
            triggered_factors.append(f"High heat index: {heat_index:.1f}°C")
        elif heat_index >= self.HEAT_THRESHOLDS['heat_index_c'][0]:
            risk_scores.append(1)
            triggered_factors.append(f"Moderate heat index: {heat_index:.1f}°C")
        else:
            risk_scores.append(0)
        
        max_score = max(risk_scores) if risk_scores else 0
        alert_level = self._score_to_alert_level(max_score)
        risk_score = max_score / 3.0
        recommendations = self._get_heat_recommendations(max_score)
        
        return alert_level, risk_score, triggered_factors + recommendations
    
    def _score_to_alert_level(self, score: int) -> str:
        """Convert risk score to alert level.
        
        Args:
            score: Risk score (0-3)
            
        Returns:
            Alert level string
        """
        if score >= 3:
            return 'DANGER'
        elif score >= 2:
            return 'WARNING'
        elif score >= 1:
            return 'WATCH'
        else:
            return 'NORMAL'
    
    def _get_flood_recommendations(self, risk_level: int) -> List[str]:
        """Get flood risk recommendations.
        
        Args:
            risk_level: Risk level (0-3)
            
        Returns:
            List of recommendations
        """
        recommendations = {
            0: [],
            1: [
                "Monitor water levels closely",
                "Prepare evacuation plans for low-lying areas"
            ],
            2: [
                "Issue flood watch - increased monitoring",
                "Alert emergency response teams",
                "Prepare temporary shelters",
                "Pre-position relief supplies"
            ],
            3: [
                "ISSUE FLOOD WARNING - immediate action required",
                "Activate emergency response protocols",
                "Begin precautionary evacuations",
                "Close low-lying roads and bridges",
                "Deploy water management resources"
            ]
        }
        return recommendations.get(risk_level, [])
    
    def _get_drought_recommendations(self, risk_level: int) -> List[str]:
        """Get drought risk recommendations.
        
        Args:
            risk_level: Risk level (0-3)
            
        Returns:
            List of recommendations
        """
        recommendations = {
            0: [],
            1: [
                "Monitor rainfall patterns",
                "Conserve water resources",
                "Plan for potential water restrictions"
            ],
            2: [
                "Declare drought watch",
                "Implement water conservation measures",
                "Support farmers with irrigation advice",
                "Increase groundwater monitoring"
            ],
            3: [
                "DECLARE DROUGHT EMERGENCY",
                "Enforce mandatory water restrictions",
                "Activate emergency water supply systems",
                "Provide emergency agricultural support",
                "Initiate food security assessments"
            ]
        }
        return recommendations.get(risk_level, [])
    
    def _get_heat_recommendations(self, risk_level: int) -> List[str]:
        """Get heat stress recommendations.
        
        Args:
            risk_level: Risk level (0-3)
            
        Returns:
            List of recommendations
        """
        recommendations = {
            0: [],
            1: [
                "Alert vulnerable populations",
                "Increase hydration messaging",
                "Open cooling centers as precaution"
            ],
            2: [
                "HEAT ALERT - reduce outdoor activities",
                "Activate cooling centers",
                "Increase health system staffing",
                "Alert media to broadcast safety messages"
            ],
            3: [
                "EXTREME HEAT EMERGENCY - restrict outdoor work",
                "Activate all cooling/shelter facilities",
                "Deploy mobile health teams",
                "Mandate workplace safety measures",
                "Increase emergency health services"
            ]
        }
        return recommendations.get(risk_level, [])
    
    def generate_alerts_for_station(
        self,
        vlcis_station_id: str,
        station_data: Dict[str, float],
        timestamp: datetime
    ) -> Dict:
        """Generate comprehensive alerts for a VLCIS station.
        
        Args:
            vlcis_station_id: VLCIS station identifier
            station_data: Station meteorological data
            timestamp: Alert timestamp
            
        Returns:
            Dictionary with all risk assessments and alerts
        """
        flood_level, flood_score, flood_info = self.assess_flood_risk(station_data)
        drought_level, drought_score, drought_info = self.assess_drought_risk(station_data)
        heat_level, heat_score, heat_info = self.assess_heat_stress_risk(station_data)
        
        alert_dict = {
            'timestamp': timestamp.isoformat(),
            'vlcis_station_id': vlcis_station_id,
            'flood_risk': {
                'alert_level': flood_level,
                'risk_score': flood_score,
                'triggered_factors': flood_info
            },
            'drought_risk': {
                'alert_level': drought_level,
                'risk_score': drought_score,
                'triggered_factors': drought_info
            },
            'heat_stress_risk': {
                'alert_level': heat_level,
                'risk_score': heat_score,
                'triggered_factors': heat_info
            },
            'overall_alert_level': self._get_overall_alert_level(flood_level, drought_level, heat_level)
        }
        
        self.alerts_history.append(alert_dict)
        return alert_dict
    
    def _get_overall_alert_level(self, flood: str, drought: str, heat: str) -> str:
        """Get overall alert level from three risk categories.
        
        Args:
            flood: Flood risk level
            drought: Drought risk level
            heat: Heat stress level
            
        Returns:
            Overall alert level
        """
        levels = {'NORMAL': 0, 'WATCH': 1, 'WARNING': 2, 'DANGER': 3}
        max_level = max(levels[flood], levels[drought], levels[heat])
        
        for level, value in levels.items():
            if value == max_level:
                return level
        return 'NORMAL'


if __name__ == '__main__':
    # Example usage
    ews = EarlyWarningSystem()
    
    # Simulate station data
    station_data = {
        'rainfall_24h_mm': 45,
        'soil_moisture_0_7cm_percent': 85,
        'cumulative_rain_7d_mm': 180,
        'rainfall_30d_deficit_percent': -10,
        'et0_ratio': 1.3,
        'wet_bulb_temperature_c': 27,
        'heat_index_c': 39
    }
    
    # Generate alert
    alert = ews.generate_alerts_for_station(
        vlcis_station_id='VLCIS_000000',
        station_data=station_data,
        timestamp=datetime.now()
    )
    
    print("Alert Generated:")
    print(json.dumps(alert, indent=2))
