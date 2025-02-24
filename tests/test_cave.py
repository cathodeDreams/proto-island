import numpy as np
import pytest
from proto_island.map import GameMap, TerrainType
from proto_island.cave import CaveGenerator, CaveParams

def test_cave_generator_initialization():
    """Test that the cave generator initializes with correct parameters."""
    params = CaveParams(
        initial_fill_probability=0.45,
        birth_limit=4,
        death_limit=3,
        iterations=4
    )
    generator = CaveGenerator(params)
    assert generator.params == params

def test_cave_generation():
    """Test that cave generation produces valid cave structures."""
    game_map = GameMap(width=50, height=50)
    params = CaveParams(
        initial_fill_probability=0.45,
        birth_limit=4,
        death_limit=3,
        iterations=4
    )
    generator = CaveGenerator(params)
    
    # Generate a cave level
    cave_level = generator.generate(width=50, height=50, seed=42)
    
    # Test dimensions
    assert cave_level.shape == (50, 50)
    
    # Test that we have both walls and open spaces
    unique_values = set(np.unique(cave_level))
    assert len(unique_values) == 2  # Should have walls and open spaces
    
    # Test deterministic generation
    cave_level2 = generator.generate(width=50, height=50, seed=42)
    assert np.array_equal(cave_level, cave_level2)
    
    # Test different seeds produce different caves
    cave_level3 = generator.generate(width=50, height=50, seed=43)
    assert not np.array_equal(cave_level, cave_level3)

def test_cave_connectivity():
    """Test that generated caves are properly connected."""
    params = CaveParams(
        initial_fill_probability=0.45,
        birth_limit=4,
        death_limit=3,
        iterations=4
    )
    generator = CaveGenerator(params)
    cave_level = generator.generate(width=50, height=50, seed=42)
    
    # Find all open spaces
    open_spaces = np.where(cave_level == 0)
    if len(open_spaces[0]) == 0:
        return  # No open spaces to test
    
    # Start flood fill from first open space
    start_y, start_x = open_spaces[0][0], open_spaces[1][0]
    visited = np.zeros_like(cave_level, dtype=bool)
    
    def flood_fill(x: int, y: int) -> None:
        if (x < 0 or x >= cave_level.shape[1] or 
            y < 0 or y >= cave_level.shape[0] or 
            visited[y, x] or cave_level[y, x] == 1):
            return
        visited[y, x] = True
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            flood_fill(x + dx, y + dy)
    
    flood_fill(start_x, start_y)
    
    # All open spaces should be connected
    for y, x in zip(*open_spaces):
        if cave_level[y, x] == 0:  # If it's an open space
            assert visited[y, x], f"Disconnected cave section found at ({x}, {y})"

def test_cave_integration():
    """Test integration of cave generation with the main map system."""
    game_map = GameMap(width=50, height=50)
    game_map.generate_terrain(seed=42)
    
    # Add an underground level
    game_map.add_z_level(-1)
    game_map.change_level(-1)
    
    # Generate and apply cave
    params = CaveParams(
        initial_fill_probability=0.45,
        birth_limit=4,
        death_limit=3,
        iterations=4
    )
    generator = CaveGenerator(params)
    cave_level = generator.generate(
        width=game_map.width,
        height=game_map.height,
        seed=42
    )
    
    # Apply cave to the underground level
    game_map.apply_cave_layout(cave_level)
    
    # Test that cave walls and floor are properly set
    unique_terrains = set(np.unique(game_map.tiles))
    assert TerrainType.CAVE_WALL in unique_terrains
    assert TerrainType.CAVE_FLOOR in unique_terrains

def test_cave_entrance_generation():
    """Test that cave entrances are properly generated and connected."""
    game_map = GameMap(width=50, height=50)
    game_map.generate_terrain(seed=42)
    
    # Add underground level
    game_map.add_z_level(-1)
    
    # Generate cave entrance
    entrance_x, entrance_y = game_map.generate_cave_entrance(seed=42)
    
    # Test that entrance coordinates are valid
    assert game_map.in_bounds(entrance_x, entrance_y)
    
    # Test that entrance is properly connected between levels
    transitions = game_map.get_level_transitions(0)
    assert -1 in transitions
    assert (entrance_x, entrance_y) in transitions[-1]
    
    # Test that entrance is properly marked on both levels
    assert game_map.tiles[entrance_y, entrance_x] == TerrainType.CAVE_ENTRANCE
    
    game_map.change_level(-1)
    transitions = game_map.get_level_transitions(-1)
    assert 0 in transitions
    assert (entrance_x, entrance_y) in transitions[0] 