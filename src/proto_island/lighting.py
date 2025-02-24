import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class LightSource(Enum):
    """Types of light sources in the game."""
    NATURAL = 1  # Sun/Moon
    ARTIFICIAL = 2  # Man-made lights
    REFLECTED = 3  # Light reflected from surfaces

@dataclass
class TimeOfDay:
    """Represents the current time of day and its lighting properties."""
    hour: int  # 0-23
    minute: int  # 0-59
    base_intensity: float  # Base light level (0.0-1.0)
    color_temperature: float  # In Kelvin, affects light color

class LightingSystem:
    """Manages the dynamic lighting system for the game world."""
    
    def __init__(self, width: int, height: int):
        """Initialize the lighting system.
        
        Args:
            width: Width of the map in tiles
            height: Height of the map in tiles
        """
        self.width = width
        self.height = height
        
        # Main lighting grid (0.0 = pitch black, 1.0 = full brightness)
        self.light_levels = np.zeros((height, width), dtype=np.float32)
        
        # Separate layers for different light sources
        self.natural_light = np.zeros((height, width), dtype=np.float32)
        self.artificial_light = np.zeros((height, width), dtype=np.float32)
        self.reflected_light = np.zeros((height, width), dtype=np.float32)
        
        # Surface reflectivity map (0.0 = no reflection, 1.0 = full reflection)
        self.reflectivity = np.zeros((height, width), dtype=np.float32)
        
        # Current time of day
        self.time = TimeOfDay(hour=12, minute=0, base_intensity=1.0, color_temperature=5500.0)
    
    def update_natural_light(self) -> None:
        """Update natural lighting based on time of day."""
        # Calculate sun position and intensity
        hour = self.time.hour + self.time.minute / 60.0
        
        # Simple day/night cycle (peaked at noon)
        if 6 <= hour < 18:  # Daytime
            # Cosine curve for smooth transition
            angle = (hour - 12) * np.pi / 12  # -π/2 at 6am, 0 at noon, π/2 at 6pm
            intensity = np.cos(angle) * 0.8 + 0.2  # Range from 0.2 to 1.0
        else:  # Nighttime
            # Base moonlight (can be modified later for moon phases)
            intensity = 0.1
        
        self.natural_light.fill(intensity)
    
    def update_surface_reflectivity(self, terrain_heightmap: np.ndarray, terrain_types: np.ndarray) -> None:
        """Update the reflectivity map based on terrain.
        
        Args:
            terrain_heightmap: 2D array of terrain height values
            terrain_types: 2D array of terrain type values
        """
        # Reset reflectivity
        self.reflectivity.fill(0.0)
        
        # Water has high reflectivity
        water_mask = terrain_types == 0  # TerrainType.WATER
        self.reflectivity[water_mask] = 0.8
        
        # Beach has medium reflectivity
        beach_mask = terrain_types == 1  # TerrainType.BEACH
        self.reflectivity[beach_mask] = 0.4
        
        # Other terrain types have lower reflectivity
        self.reflectivity[~(water_mask | beach_mask)] = 0.1
    
    def calculate_reflected_light(self) -> None:
        """Calculate reflected light based on surface properties and current lighting."""
        # Reflected light is based on natural light and surface reflectivity
        self.reflected_light = self.natural_light * self.reflectivity
    
    def update(self) -> None:
        """Update the entire lighting system."""
        self.update_natural_light()
        self.calculate_reflected_light()
        
        # Combine natural light and a fraction of reflected light and artificial light additively
        self.light_levels = self.natural_light + 0.3 * self.reflected_light + self.artificial_light
        np.clip(self.light_levels, 0.0, 1.0, out=self.light_levels)
    
    def get_light_level(self, x: int, y: int) -> float:
        """Get the light level at a specific position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            float: Light level from 0.0 to 1.0
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.light_levels[y, x]
        return 0.0 