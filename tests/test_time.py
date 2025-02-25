import pytest
import numpy as np
from proto_island.time import TimeSystem, WeatherCondition

def test_time_system_initialization():
    """Test that time system initializes correctly."""
    time_system = TimeSystem()
    assert time_system.hour == 12
    assert time_system.minute == 0
    assert time_system.day == 0
    assert time_system.moon_phase == 0
    assert time_system.weather_condition == WeatherCondition.CLEAR

def test_time_advancement():
    """Test that time advances correctly."""
    time_system = TimeSystem(hour=23, minute=45)
    time_system.advance(30)  # 30 minutes
    assert time_system.hour == 0
    assert time_system.minute == 15
    assert time_system.day == 1  # Day should advance

def test_multi_day_advancement():
    """Test advancing multiple days."""
    time_system = TimeSystem(hour=12, minute=0)
    time_system.advance(60 * 48)  # Advance 48 hours
    assert time_system.hour == 12
    assert time_system.minute == 0
    assert time_system.day == 2

def test_daylight_factor():
    """Test daylight factor calculation."""
    # Noon = maximum light
    time_system = TimeSystem(hour=12, minute=0)
    assert time_system.get_daylight_factor() == pytest.approx(1.0, abs=0.01)
    
    # Midnight = no sunlight
    time_system = TimeSystem(hour=0, minute=0)
    assert time_system.get_daylight_factor() == 0.0
    
    # Dawn/dusk = partial light
    time_system = TimeSystem(hour=6, minute=0)  # Dawn
    dawn_light = time_system.get_daylight_factor()
    print(f"Dawn light at 6:00 = {dawn_light}")
    
    # Test just after dawn
    time_system = TimeSystem(hour=6, minute=1)  # Just after dawn
    dawn_plus_one = time_system.get_daylight_factor()
    print(f"Dawn light at 6:01 = {dawn_plus_one}")
    
    # Ensure some light at dawn
    assert dawn_light >= 0.0
    assert dawn_plus_one > 0.0
    
    # Just before dawn should be dark
    time_system = TimeSystem(hour=5, minute=59)
    predawn = time_system.get_daylight_factor()
    print(f"Pre-dawn light at 5:59 = {predawn}")
    assert predawn == 0.0

def test_moon_illumination():
    """Test moon illumination calculation."""
    # Full moon at midnight
    time_system = TimeSystem(hour=0, minute=0)
    time_system.moon_phase = 0
    full_moon = time_system.get_moon_illumination()
    
    # New moon at midnight
    time_system.moon_phase = 4
    new_moon = time_system.get_moon_illumination()
    
    # Full moon should be brighter than new moon
    assert full_moon > new_moon
    
    # Daytime = no moonlight
    time_system = TimeSystem(hour=12, minute=0)
    time_system.moon_phase = 0
    assert time_system.get_moon_illumination() == 0.0

def test_weather_light_modifier():
    """Test weather effects on light."""
    time_system = TimeSystem()
    
    # Clear weather should have maximum light transmission
    time_system.weather_condition = WeatherCondition.CLEAR
    clear_mod = time_system.get_weather_light_modifier()
    
    # Stormy weather should reduce light
    time_system.weather_condition = WeatherCondition.STORMY
    stormy_mod = time_system.get_weather_light_modifier()
    
    assert clear_mod > stormy_mod

def test_moon_phase_advancement():
    """Test moon phase advances with days."""
    time_system = TimeSystem()
    initial_phase = time_system.moon_phase
    
    # Advance several days
    for _ in range(3):
        time_system.advance_day()
    
    # Moon phase should change
    assert time_system.moon_phase != initial_phase

def test_weather_transition():
    """Test weather transitions occur."""
    # Use fixed seed for deterministic test
    np.random.seed(42)
    
    time_system = TimeSystem()
    initial_weather = time_system.weather_condition
    
    # Force a weather transition
    time_system.weather_duration = 0
    time_system._select_new_weather()
    
    # Verify transition was set up
    assert time_system.weather_transition is not None

def test_get_star_positions():
    """Test star position calculation."""
    time_system = TimeSystem(hour=0, minute=0)  # Midnight
    positions = time_system.get_star_positions()
    
    # Should have some stars
    assert len(positions) > 0
    
    # No stars during day
    time_system = TimeSystem(hour=12, minute=0)
    day_positions = time_system.get_star_positions()
    assert len(day_positions) == 0
    
    # Different days should have slightly different star patterns
    time_system = TimeSystem(hour=0, minute=0, initial_day=0)
    day1_positions = time_system.get_star_positions()
    
    time_system = TimeSystem(hour=0, minute=0, initial_day=10)
    day10_positions = time_system.get_star_positions()
    
    # Stars should shift position over time
    assert day1_positions != day10_positions 