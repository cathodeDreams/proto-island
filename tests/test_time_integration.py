import pytest
import numpy as np
from proto_island.map import GameMap
from proto_island.lighting import LightingSystem
from proto_island.time import TimeSystem, WeatherCondition

def test_map_time_system_integration():
    """Test that the TimeSystem is properly integrated with GameMap."""
    game_map = GameMap(50, 50)
    
    # Check time system was created
    assert game_map.time_system is not None
    assert isinstance(game_map.time_system, TimeSystem)
    
    # Check time system was connected to lighting
    assert game_map.lighting.time_system is not None
    assert game_map.lighting.time_system is game_map.time_system

def test_set_time_updates_lighting():
    """Test that setting time updates lighting accordingly."""
    game_map = GameMap(50, 50)
    
    # Set to noon (maximum light)
    game_map.set_time(12, 0)
    noon_light = game_map.get_light_level(25, 25)
    
    # Set to midnight (minimum light)
    game_map.set_time(0, 0)
    midnight_light = game_map.get_light_level(25, 25)
    
    # Noon should be brighter than midnight
    assert noon_light > midnight_light

def test_advance_time():
    """Test advancing time updates game state correctly."""
    game_map = GameMap(50, 50)
    game_map.set_time(23, 30)  # 11:30 PM
    
    # Advance by 45 minutes
    game_map.advance_time(45)
    
    hour, minute = game_map.get_current_time()
    assert hour == 0
    assert minute == 15
    
    # Day should have advanced
    assert game_map.time_system.day == 1

def test_z_level_lighting_consistency():
    """Test that all z-levels share the same time system."""
    game_map = GameMap(50, 50)
    
    # Add a new z-level
    game_map.add_z_level(1)
    
    # Set time
    game_map.set_time(12, 0)
    
    # Change to new z-level
    game_map.change_level(1)
    
    # Check time is consistent
    assert game_map.time_system.hour == 12
    assert game_map.time_system.minute == 0
    
    # Check lighting uses same time system
    assert game_map.lighting.time_system is game_map.time_system

def test_weather_affects_lighting():
    """Test that weather conditions affect lighting levels."""
    game_map = GameMap(50, 50)
    
    # Set to noon with clear weather
    game_map.set_time(12, 0)
    game_map.time_system.weather_condition = WeatherCondition.CLEAR
    game_map.update_lighting()
    clear_light = game_map.get_light_level(25, 25)
    
    # Change to stormy weather
    game_map.time_system.weather_condition = WeatherCondition.STORMY
    game_map.update_lighting()
    stormy_light = game_map.get_light_level(25, 25)
    
    # Clear weather should be brighter
    assert clear_light > stormy_light

def test_moon_phase_affects_night_lighting():
    """Test that moon phases affect nighttime lighting."""
    game_map = GameMap(50, 50)
    
    # Midnight with full moon
    game_map.set_time(0, 0)
    game_map.time_system.moon_phase = 0  # Full moon
    
    # Directly check moon illumination factor
    full_moon_factor = game_map.time_system.get_moon_illumination()
    print(f"Full moon illumination factor: {full_moon_factor}")
    
    # Update lighting and check levels
    game_map.update_lighting()
    full_moon_light = game_map.get_light_level(25, 25)
    print(f"Full moon light level: {full_moon_light}")
    
    # Midnight with new moon
    game_map.time_system.moon_phase = 4  # New moon
    
    # Directly check moon illumination factor
    new_moon_factor = game_map.time_system.get_moon_illumination()
    print(f"New moon illumination factor: {new_moon_factor}")
    
    # Update lighting and check levels
    game_map.update_lighting()
    new_moon_light = game_map.get_light_level(25, 25)
    print(f"New moon light level: {new_moon_light}")
    
    # Full moon should be brighter at the time system level
    assert full_moon_factor > new_moon_factor
    
    # Full moon should be brighter at the final light level
    assert full_moon_light > new_moon_light 