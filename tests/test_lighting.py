import numpy as np
import pytest
from proto_island.lighting import LightingSystem, TimeOfDay, LightSource

def test_lighting_system_initialization():
    """Test that the lighting system initializes correctly."""
    width, height = 100, 100
    lighting = LightingSystem(width, height)
    
    assert lighting.width == width
    assert lighting.height == height
    assert lighting.light_levels.shape == (height, width)
    assert lighting.natural_light.shape == (height, width)
    assert lighting.artificial_light.shape == (height, width)
    assert lighting.reflected_light.shape == (height, width)
    assert lighting.reflectivity.shape == (height, width)
    assert np.all(lighting.light_levels == 0.0)

def test_natural_light_day_cycle():
    """Test that natural light changes correctly with time of day."""
    lighting = LightingSystem(10, 10)
    
    # Test noon (brightest)
    lighting.time = TimeOfDay(hour=12, minute=0, base_intensity=1.0, color_temperature=5500.0)
    lighting.update_natural_light()
    assert np.all(lighting.natural_light == 1.0)
    
    # Test midnight (darkest)
    lighting.time = TimeOfDay(hour=0, minute=0, base_intensity=1.0, color_temperature=5500.0)
    lighting.update_natural_light()
    assert np.all(lighting.natural_light == 0.1)  # Base moonlight
    
    # Test dawn/dusk (intermediate)
    lighting.time = TimeOfDay(hour=6, minute=0, base_intensity=1.0, color_temperature=5500.0)
    lighting.update_natural_light()
    assert np.all(lighting.natural_light == pytest.approx(0.2, abs=0.1))

def test_surface_reflectivity():
    """Test that surface reflectivity is calculated correctly."""
    lighting = LightingSystem(10, 10)
    
    # Create mock terrain data
    terrain_heightmap = np.zeros((10, 10))
    terrain_types = np.zeros((10, 10))  # All water initially; water is represented by 0
    
    # Test water reflectivity
    lighting.update_surface_reflectivity(terrain_heightmap, terrain_types)
    assert np.all(lighting.reflectivity == 0.8)
    
    # Test beach reflectivity
    terrain_types.fill(1)  # All beach; beach is represented by 1
    lighting.update_surface_reflectivity(terrain_heightmap, terrain_types)
    assert np.all(lighting.reflectivity == 0.4)
    
    # Test mixed terrain
    terrain_types[:5] = 0  # Upper half water; water is represented by 0
    terrain_types[5:] = 1  # Lower half beach; beach is represented by 1
    lighting.update_surface_reflectivity(terrain_heightmap, terrain_types)
    assert np.all(lighting.reflectivity[:5] == 0.8)
    assert np.all(lighting.reflectivity[5:] == 0.4)

def test_light_level_bounds():
    """Test that light levels stay within valid bounds."""
    lighting = LightingSystem(10, 10)
    
    # Set extreme values
    lighting.natural_light.fill(2.0)
    lighting.artificial_light.fill(0.5)
    lighting.reflected_light.fill(0.7)
    
    # Update should clamp values
    lighting.update()
    assert np.all(lighting.light_levels <= 1.0)
    assert np.all(lighting.light_levels >= 0.0)

def test_get_light_level():
    """Test getting light levels at specific coordinates."""
    lighting = LightingSystem(10, 10)
    
    # Set a known light level
    lighting.light_levels[5, 5] = 0.75
    
    # Test valid coordinates
    assert lighting.get_light_level(5, 5) == 0.75
    
    # Test out of bounds coordinates
    assert lighting.get_light_level(-1, 5) == 0.0
    assert lighting.get_light_level(5, 10) == 0.0
    assert lighting.get_light_level(10, 10) == 0.0 