import pytest
import numpy as np
import tcod
from proto_island.map import GameMap, TerrainType

def test_map_initialization():
    """Test basic map initialization with correct dimensions and terrain types."""
    map_width = 200
    map_height = 200
    game_map = GameMap(width=map_width, height=map_height)
    
    # Test map dimensions
    assert game_map.width == map_width
    assert game_map.height == map_height
    
    # Test that the map array is properly initialized
    assert game_map.tiles.shape == (map_height, map_width)
    
    # Test that all tiles are initialized to a valid terrain type
    assert all(tile in TerrainType for tile in np.unique(game_map.tiles))

def test_terrain_types():
    """Test that all required terrain types are defined."""
    required_types = {'WATER', 'BEACH', 'GRASS', 'ROCK', 'FOREST'}
    terrain_types = {t.name for t in TerrainType}
    assert required_types.issubset(terrain_types)

def test_map_bounds():
    """Test that map coordinates are properly bounded."""
    game_map = GameMap(width=200, height=200)
    
    # Test in-bounds coordinates
    assert game_map.in_bounds(0, 0)
    assert game_map.in_bounds(199, 199)
    
    # Test out-of-bounds coordinates
    assert not game_map.in_bounds(-1, 0)
    assert not game_map.in_bounds(0, -1)
    assert not game_map.in_bounds(200, 0)
    assert not game_map.in_bounds(0, 200)

def test_terrain_generation():
    """Test that terrain generation produces valid and varied terrain."""
    game_map = GameMap(width=200, height=200)
    game_map.generate_terrain(seed=42)
    
    # Test that we have all terrain types present
    unique_terrains = set(np.unique(game_map.tiles))
    assert TerrainType.WATER in unique_terrains
    assert TerrainType.BEACH in unique_terrains
    assert TerrainType.GRASS in unique_terrains
    
    # Test that terrain is varied (not all one type)
    surface_types = [TerrainType.WATER, TerrainType.BEACH, TerrainType.GRASS, TerrainType.ROCK, TerrainType.FOREST]
    terrain_counts = {terrain: np.sum(game_map.tiles == terrain) for terrain in surface_types}
    assert all(count > 0 for count in terrain_counts.values()), "All surface terrain types should be present"
    
    # Test that terrain generation is deterministic with same seed
    game_map2 = GameMap(width=200, height=200)
    game_map2.generate_terrain(seed=42)
    assert np.array_equal(game_map.tiles, game_map2.tiles)
    
    # Test that different seeds produce different terrains
    game_map3 = GameMap(width=200, height=200)
    game_map3.generate_terrain(seed=43)
    assert not np.array_equal(game_map.tiles, game_map3.tiles)

def test_terrain_features():
    """Test that terrain features like hills and erosion are properly generated."""
    game_map = GameMap(width=200, height=200)
    game_map.generate_terrain(seed=42)
    
    # Get heightmap before and after adding features
    heightmap_before = game_map.get_heightmap()
    game_map.add_terrain_features(seed=42)
    heightmap_after = game_map.get_heightmap()
    
    # Test that features actually modified the terrain
    assert not np.array_equal(heightmap_before, heightmap_after)
    
    # Test that terrain variation has increased
    std_before = np.std(heightmap_before)
    std_after = np.std(heightmap_after)
    assert std_after > std_before, "Terrain features should increase height variation"
    
    # Test that we have more local maxima after adding hills
    def count_local_maxima(heightmap):
        maxima = 0
        for y in range(1, game_map.height-1):
            for x in range(1, game_map.width-1):
                neighbors = [
                    heightmap[y-1:y+2, x-1:x+2]
                ]
                if np.all(heightmap[y,x] >= neighbors):
                    maxima += 1
        return maxima
    
    maxima_before = count_local_maxima(heightmap_before)
    maxima_after = count_local_maxima(heightmap_after)
    assert maxima_after > maxima_before, "Adding hills should create more local maxima"

def test_lighting_integration():
    """Test that lighting system is properly integrated with the map."""
    game_map = GameMap(100, 100)
    
    # Test initial state
    assert game_map.lighting is not None
    assert game_map.get_light_level(50, 50) == 0.0  # Should start dark
    
    # Test time changes affect lighting
    game_map.set_time(12, 0)  # Noon
    game_map.update_lighting()
    assert game_map.get_light_level(50, 50) == 1.0  # Should be brightest
    
    game_map.set_time(0, 0)  # Midnight
    game_map.update_lighting()
    assert game_map.get_light_level(50, 50) == 0.1  # Should be moonlight level

def test_terrain_lighting_interaction():
    """Test that different terrain types interact correctly with lighting."""
    game_map = GameMap(10, 10)
    
    # Generate terrain
    game_map.generate_terrain(seed=42)
    
    # Set to 8:00 for consistent lighting (not saturating)
    game_map.set_time(8, 0)
    game_map.update_lighting()
    
    # Find water and beach tiles
    water_y, water_x = np.where(game_map.tiles == TerrainType.WATER)[0:2]
    beach_y, beach_x = np.where(game_map.tiles == TerrainType.BEACH)[0:2]
    
    if len(water_x) > 0 and len(beach_x) > 0:
        # Water should reflect more light than beach
        water_light = game_map.get_light_level(water_x[0], water_y[0])
        beach_light = game_map.get_light_level(beach_x[0], beach_y[0])
        assert water_light > beach_light

class TestZLevels:
    """Test suite for z-level functionality."""
    
    def test_z_level_initialization(self):
        """Test that z-levels can be created and accessed."""
        game_map = GameMap(width=100, height=100)
        
        # Test initial state
        assert game_map.current_z == 0
        assert len(game_map.z_levels) == 1
        
        # Test adding new z-level above
        game_map.add_z_level(1)  # Add level above
        assert len(game_map.z_levels) == 2
        assert 1 in game_map.z_levels
        
        # Test adding new z-level below
        game_map.add_z_level(-1)  # Add underground level
        assert len(game_map.z_levels) == 3
        assert -1 in game_map.z_levels
    
    def test_z_level_navigation(self):
        """Test moving between z-levels."""
        game_map = GameMap(width=100, height=100)
        
        # Add levels
        game_map.add_z_level(1)
        game_map.add_z_level(-1)
        
        # Test navigation
        assert game_map.current_z == 0
        
        game_map.change_level(1)
        assert game_map.current_z == 1
        
        game_map.change_level(-1)  # Direct movement between levels
        assert game_map.current_z == -1
        
        game_map.change_level(0)  # Return to surface
        assert game_map.current_z == 0
        
        # Test invalid navigation
        with pytest.raises(ValueError):
            game_map.change_level(2)  # Level doesn't exist
    
    def test_z_level_state_persistence(self):
        """Test that each z-level maintains its own state."""
        game_map = GameMap(width=100, height=100)
        game_map.generate_terrain(seed=42)
        
        # Store initial surface state
        surface_terrain = game_map.tiles.copy()
        
        # Add and generate new level
        game_map.add_z_level(1)
        game_map.change_level(1)
        game_map.generate_terrain(seed=43)
        
        # Verify levels have different terrain
        assert not np.array_equal(game_map.tiles, surface_terrain)
        
        # Return to surface and verify state persisted
        game_map.change_level(0)
        assert np.array_equal(game_map.tiles, surface_terrain)
    
    def test_z_level_connectivity(self):
        """Test that z-levels can be connected via stairs/transitions."""
        game_map = GameMap(width=100, height=100)
        game_map.add_z_level(1)
        game_map.add_z_level(-1)
        
        # Add connections
        surface_up = (10, 10)
        surface_down = (20, 20)
        game_map.add_level_transition(0, 1, surface_up[0], surface_up[1])
        game_map.add_level_transition(0, -1, surface_down[0], surface_down[1])
        
        # Test connection queries
        assert game_map.get_level_transitions(0) == {
            1: [(surface_up[0], surface_up[1])],
            -1: [(surface_down[0], surface_down[1])]
        }
        
        # Test reciprocal connections were created
        assert game_map.get_level_transitions(1) == {
            0: [(surface_up[0], surface_up[1])]
        }
        assert game_map.get_level_transitions(-1) == {
            0: [(surface_down[0], surface_down[1])]
        } 