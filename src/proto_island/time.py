import math
import numpy as np
from enum import Enum, auto

class WeatherCondition(Enum):
    CLEAR = auto()
    PARTLY_CLOUDY = auto()
    CLOUDY = auto()
    FOGGY = auto()
    RAINY = auto()
    STORMY = auto()

class TimeSystem:
    def __init__(self, hour=12, minute=0, initial_day=0):
        self.hour = hour
        self.minute = minute
        self.day = initial_day
        self.moon_phase = initial_day % 8  # 8 moon phases
        self.weather_condition = WeatherCondition.CLEAR
        self.weather_transition = None  # For gradual weather changes
        self.weather_duration = np.random.uniform(4, 12)  # Hours until weather might change
        
        # Star configuration
        self.star_seed = 42  # Base seed for star generation
        self.constellation_count = 12
        self.star_count = 100
        
    def advance(self, minutes):
        """Advance time by specified minutes."""
        total_minutes = self.hour * 60 + self.minute + minutes
        new_days = total_minutes // (24 * 60)
        total_minutes %= (24 * 60)
        
        self.hour = total_minutes // 60
        self.minute = total_minutes % 60
        
        if new_days > 0:
            # Advance multiple days if needed
            for _ in range(new_days):
                self.advance_day()
        
        # Check for weather changes
        self.update_weather(minutes / 60)  # Convert to hours
    
    def advance_day(self):
        """Advance to the next day and update moon phase."""
        self.day += 1
        # Update moon phase every 3 days
        if self.day % 3 == 0:
            self.moon_phase = (self.moon_phase + 1) % 8
    
    def update_weather(self, elapsed_hours):
        """Update weather conditions based on time passage."""
        self.weather_duration -= elapsed_hours
        
        # If weather transition is in progress, continue it
        if self.weather_transition:
            if self.weather_duration <= 0:
                self.weather_condition = self.weather_transition
                self.weather_transition = None
                self.weather_duration = np.random.uniform(4, 12)  # Hours until next change
        # Possibly start a new weather change
        elif self.weather_duration <= 0:
            # 30% chance of weather changing when timer expires
            if np.random.random() < 0.3:
                self._select_new_weather()
            else:
                # Reset timer but keep same weather
                self.weather_duration = np.random.uniform(2, 8)
    
    def _select_new_weather(self):
        """Select a new weather condition based on current one."""
        # Different weather patterns have different probabilities
        # based on current weather
        weather_options = list(WeatherCondition)
        weights = self._get_weather_weights()
        
        # Choose new weather
        self.weather_transition = np.random.choice(weather_options, p=weights)
        # Set transition duration
        self.weather_duration = np.random.uniform(0.5, 2)  # Transition hours
    
    def _get_weather_weights(self):
        """Get probability weights for next weather based on current."""
        weights = {cond: 0.0 for cond in WeatherCondition}
        
        # Default: weather tends to stay the same
        weights[self.weather_condition] = 0.6
        
        # Specific transitions based on current weather
        if self.weather_condition == WeatherCondition.CLEAR:
            weights[WeatherCondition.PARTLY_CLOUDY] = 0.3
            weights[WeatherCondition.FOGGY] = 0.1
        elif self.weather_condition == WeatherCondition.PARTLY_CLOUDY:
            weights[WeatherCondition.CLEAR] = 0.2
            weights[WeatherCondition.CLOUDY] = 0.2
        elif self.weather_condition == WeatherCondition.CLOUDY:
            weights[WeatherCondition.PARTLY_CLOUDY] = 0.1
            weights[WeatherCondition.RAINY] = 0.2
            weights[WeatherCondition.FOGGY] = 0.1
        elif self.weather_condition == WeatherCondition.RAINY:
            weights[WeatherCondition.CLOUDY] = 0.2
            weights[WeatherCondition.STORMY] = 0.2
        elif self.weather_condition == WeatherCondition.STORMY:
            weights[WeatherCondition.RAINY] = 0.4
        elif self.weather_condition == WeatherCondition.FOGGY:
            weights[WeatherCondition.CLEAR] = 0.2
            weights[WeatherCondition.PARTLY_CLOUDY] = 0.2
            
        # Normalize weights to sum to 1.0
        total = sum(weights.values())
        return [weights[cond] / total for cond in WeatherCondition]
    
    def get_daylight_factor(self):
        """Return daylight factor (0.0 to 1.0) based on time of day."""
        # No sunlight during night hours (18:00 - 6:00)
        if self.hour > 18 or self.hour < 6:
            return 0.0
        
        # Calculate daylight hours (6:00 - 18:00)
        hour_factor = (self.hour + self.minute / 60.0 - 6) / 12.0  # 0.0 to 1.0 over daylight hours
        
        # Sinusoidal curve for natural light variation (peak at noon)
        result = math.sin(hour_factor * math.pi)
        return result
    
    def get_moon_illumination(self):
        """Return moon illumination factor based on phase and time."""
        # Moon only visible at night
        if 6 <= self.hour < 18:
            return 0.0
        
        # Calculate base illumination based on phase
        # Phase 0 = full moon, Phase 4 = new moon
        phase_factor = 1.0 - (self.moon_phase / 4.0 if self.moon_phase <= 4 
                              else (8 - self.moon_phase) / 4.0)
        
        # Enhance the moon phase effect - make full moon brighter, new moon darker
        phase_factor = phase_factor ** 0.5  # Exponent < 1 increases contrast
        
        # Calculate position in night sky (0.0 at 18:00 and 6:00, 1.0 at midnight)
        hour_in_night = (self.hour + self.minute / 60.0)
        if hour_in_night < 6:  # After midnight (0-6)
            hour_factor = (6 - hour_in_night) / 6.0
        else:  # Before midnight (18-24)
            hour_factor = (hour_in_night - 18) / 6.0
            
        # Special case for exactly midnight - full illumination
        if hour_in_night == 0.0:
            hour_factor = 1.0
            
        # Sinusoidal curve for moon position (peak at midnight)
        position_factor = math.sin(hour_factor * math.pi)
        
        # Ensure midnight has proper illumination
        if hour_in_night == 0.0:
            position_factor = 1.0
            
        # Combine phase and position with a higher base factor
        return 0.4 * phase_factor * position_factor
    
    def get_weather_light_modifier(self):
        """Return modifier for light based on weather conditions."""
        if self.weather_condition == WeatherCondition.CLEAR:
            return 1.0
        elif self.weather_condition == WeatherCondition.PARTLY_CLOUDY:
            return 0.8
        elif self.weather_condition == WeatherCondition.CLOUDY:
            return 0.6
        elif self.weather_condition == WeatherCondition.FOGGY:
            return 0.4
        elif self.weather_condition == WeatherCondition.RAINY:
            return 0.5
        elif self.weather_condition == WeatherCondition.STORMY:
            return 0.3
        
        # Default
        return 1.0
    
    def get_star_positions(self):
        """Return star positions based on time and day."""
        # Only visible at night
        if 6 <= self.hour < 18:
            return []
        
        # Use deterministic randomness based on day
        rng = np.random.RandomState(self.star_seed + self.day)
        
        # Generate star positions
        stars = []
        for _ in range(self.star_count):
            x = rng.uniform(0, 1)
            y = rng.uniform(0, 1)
            brightness = rng.uniform(0.1, 1.0)
            stars.append((x, y, brightness))
            
        # Generate constellations
        constellations = []
        for i in range(self.constellation_count):
            # Each constellation has 4-7 stars
            size = rng.randint(4, 8)
            # Center point
            cx = rng.uniform(0.1, 0.9)
            cy = rng.uniform(0.1, 0.9)
            # Create stars in pattern
            pattern = []
            for j in range(size):
                angle = j * (2 * math.pi / size) + rng.uniform(0, 0.5)
                distance = rng.uniform(0.02, 0.1)
                x = cx + math.cos(angle) * distance
                y = cy + math.sin(angle) * distance
                brightness = rng.uniform(0.6, 1.0)  # Constellations are brighter
                pattern.append((x, y, brightness))
            constellations.append(pattern)
            
        # Combine all stars
        for constellation in constellations:
            stars.extend(constellation)
            
        return stars 