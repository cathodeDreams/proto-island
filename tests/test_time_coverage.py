import pytest
import numpy as np
import math
from proto_island.time import TimeSystem, WeatherCondition

def test_weather_selection_with_controlled_randomness():
    """Test the _select_new_weather method with controlled randomness."""
    # Use a fixed seed for deterministic test
    np.random.seed(42)
    
    # Test for each possible initial weather condition
    for initial_weather in WeatherCondition:
        time_system = TimeSystem()
        time_system.weather_condition = initial_weather
        
        # Call the method directly
        time_system._select_new_weather()
        
        # Verify a transition was set up
        assert time_system.weather_transition is not None
        assert isinstance(time_system.weather_transition, WeatherCondition)
        
        # Verify transition duration is within expected range
        assert 0.5 <= time_system.weather_duration <= 2.0

def test_weather_weights_for_all_conditions():
    """Test that weather weights are calculated correctly for all conditions."""
    time_system = TimeSystem()
    
    # Test for each possible weather condition
    for weather in WeatherCondition:
        time_system.weather_condition = weather
        weights = time_system._get_weather_weights()
        
        # Check that weights are correctly normalized
        assert len(weights) == len(WeatherCondition)
        assert math.isclose(sum(weights), 1.0, abs_tol=1e-6)
        
        # All weights should be non-negative
        assert all(w >= 0 for w in weights)
        
        # Current weather should have highest probability
        current_idx = list(WeatherCondition).index(weather)
        assert weights[current_idx] == max(weights)

def test_specific_weather_transitions():
    """Test the specific weather transition probabilities from each condition."""
    time_system = TimeSystem()
    
    # Test CLEAR weather transitions
    time_system.weather_condition = WeatherCondition.CLEAR
    weights = time_system._get_weather_weights()
    weather_list = list(WeatherCondition)
    
    # CLEAR should transition mainly to PARTLY_CLOUDY and itself
    assert weights[weather_list.index(WeatherCondition.PARTLY_CLOUDY)] > weights[weather_list.index(WeatherCondition.CLOUDY)]
    assert weights[weather_list.index(WeatherCondition.FOGGY)] > 0
    
    # Test PARTLY_CLOUDY weather transitions
    time_system.weather_condition = WeatherCondition.PARTLY_CLOUDY
    weights = time_system._get_weather_weights()
    
    # PARTLY_CLOUDY should transition to CLEAR, CLOUDY, and itself
    assert weights[weather_list.index(WeatherCondition.CLEAR)] > 0
    assert weights[weather_list.index(WeatherCondition.CLOUDY)] > 0
    
    # Test CLOUDY weather transitions
    time_system.weather_condition = WeatherCondition.CLOUDY
    weights = time_system._get_weather_weights()
    
    # CLOUDY should transition to PARTLY_CLOUDY, RAINY, FOGGY, and itself
    assert weights[weather_list.index(WeatherCondition.PARTLY_CLOUDY)] > 0
    assert weights[weather_list.index(WeatherCondition.RAINY)] > 0
    assert weights[weather_list.index(WeatherCondition.FOGGY)] > 0
    
    # Test RAINY weather transitions
    time_system.weather_condition = WeatherCondition.RAINY
    weights = time_system._get_weather_weights()
    
    # RAINY should transition to CLOUDY, STORMY, and itself
    assert weights[weather_list.index(WeatherCondition.CLOUDY)] > 0
    assert weights[weather_list.index(WeatherCondition.STORMY)] > 0
    
    # Test STORMY weather transitions
    time_system.weather_condition = WeatherCondition.STORMY
    weights = time_system._get_weather_weights()
    
    # STORMY should transition to RAINY and itself
    assert weights[weather_list.index(WeatherCondition.RAINY)] > 0
    
    # Test FOGGY weather transitions
    time_system.weather_condition = WeatherCondition.FOGGY
    weights = time_system._get_weather_weights()
    
    # FOGGY should transition to CLEAR, PARTLY_CLOUDY, and itself
    assert weights[weather_list.index(WeatherCondition.CLEAR)] > 0
    assert weights[weather_list.index(WeatherCondition.PARTLY_CLOUDY)] > 0

def test_moon_illumination_at_exact_midnight():
    """Test the special case for moon illumination at exactly midnight."""
    # Test with full moon at exactly midnight
    time_system = TimeSystem(hour=0, minute=0)
    time_system.moon_phase = 0  # Full moon
    
    midnight_illumination = time_system.get_moon_illumination()
    
    # Test slightly before midnight (23:59)
    time_system.hour = 23
    time_system.minute = 59
    before_midnight = time_system.get_moon_illumination()
    
    # Test slightly after midnight (00:01)
    time_system.hour = 0
    time_system.minute = 1
    after_midnight = time_system.get_moon_illumination()
    
    # Midnight should be maximum illumination
    assert midnight_illumination > before_midnight
    assert midnight_illumination > after_midnight
    
    # Test with new moon at midnight
    time_system = TimeSystem(hour=0, minute=0)
    time_system.moon_phase = 4  # New moon
    new_moon_midnight = time_system.get_moon_illumination()
    
    # New moon should have zero illumination (phase 4 = new moon = no illumination)
    assert new_moon_midnight == 0.0
    # Full moon should be brighter than new moon
    assert midnight_illumination > new_moon_midnight

def test_all_weather_light_modifiers():
    """Test that all weather conditions return appropriate light modifiers."""
    time_system = TimeSystem()
    
    # Test each weather condition
    expected_values = {
        WeatherCondition.CLEAR: 1.0,
        WeatherCondition.PARTLY_CLOUDY: 0.8,
        WeatherCondition.CLOUDY: 0.6,
        WeatherCondition.FOGGY: 0.4,
        WeatherCondition.RAINY: 0.5,
        WeatherCondition.STORMY: 0.3
    }
    
    for weather, expected in expected_values.items():
        time_system.weather_condition = weather
        assert time_system.get_weather_light_modifier() == expected

def test_star_positions_day_night():
    """Test that stars are only visible at night."""
    # Test night hours
    night_hours = [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
    for hour in night_hours:
        time_system = TimeSystem(hour=hour, minute=0)
        stars = time_system.get_star_positions()
        assert len(stars) > 0
    
    # Test day hours
    day_hours = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    for hour in day_hours:
        time_system = TimeSystem(hour=hour, minute=0)
        stars = time_system.get_star_positions()
        assert len(stars) == 0

def test_star_positions_structure():
    """Test the structure of star positions data."""
    time_system = TimeSystem(hour=0, minute=0)  # Midnight
    stars = time_system.get_star_positions()
    
    # Check that output has the right structure
    assert len(stars) > 0
    for star in stars:
        # Each star should be a tuple of (x, y, brightness)
        assert len(star) == 3
        x, y, brightness = star
        
        # Values should be within expected ranges
        assert 0 <= x <= 1
        assert 0 <= y <= 1
        assert 0.1 <= brightness <= 1.0

def test_update_weather_transition():
    """Test the weather transition process over time."""
    np.random.seed(42)  # For deterministic testing
    
    time_system = TimeSystem()
    initial_weather = time_system.weather_condition
    
    # Start a transition
    time_system.weather_duration = 0
    time_system._select_new_weather()
    transition_target = time_system.weather_transition
    
    # Partial advancement (not enough to complete transition)
    partial_time = time_system.weather_duration / 2
    time_system.update_weather(partial_time)
    
    # Weather should not have changed yet
    assert time_system.weather_condition == initial_weather
    assert time_system.weather_transition == transition_target
    
    # Complete the transition
    time_system.update_weather(time_system.weather_duration + 0.1)
    
    # Weather should now be updated and transition cleared
    assert time_system.weather_condition == transition_target
    assert time_system.weather_transition is None
    
    # Duration should be reset for next potential change
    assert time_system.weather_duration > 0 