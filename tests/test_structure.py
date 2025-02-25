import pytest
import numpy as np
from pytest import approx

from proto_island.structure import StructureType, StructureGenerator
from proto_island.map import GameMap, TerrainType

class TestStructureGenerator:
    """Tests for the structure generation system."""
    
    def test_structure_generator_initialization(self):
        """Test basic initialization of the structure generator."""
        generator = StructureGenerator(width=50, height=50)
        assert generator.width == 50
        assert generator.height == 50
        
    def test_structure_type_enum(self):
        """Test the structure type enumeration."""
        assert StructureType.HOUSE < StructureType.SHOP
        assert StructureType.SHOP < StructureType.TEMPLE
        
    def test_building_placement_constraints(self):
        """Test that buildings are only placed on valid terrain."""
        # Create a map with mixed terrain
        game_map = GameMap(width=50, height=50)
        # Set specific terrain types for testing
        test_terrain = np.full((50, 50), TerrainType.GRASS, dtype=object)
        # Create water and steep areas where buildings shouldn't be placed
        test_terrain[0:10, 0:10] = TerrainType.WATER
        test_terrain[40:50, 40:50] = TerrainType.ROCK
        
        # Apply our test terrain
        game_map.z_levels[0]['tiles'] = test_terrain
        
        # Initialize structure generator
        generator = StructureGenerator(width=50, height=50)
        
        # Generate buildings
        buildings = generator.generate_buildings(game_map, count=5, seed=42)
        
        # Check that no buildings are placed in invalid areas
        for building in buildings:
            x, y, w, h = building['footprint']
            building_terrain = test_terrain[y:y+h, x:x+w]
            # Buildings should only be on GRASS, BEACH, or similar suitable terrain
            assert not np.any(building_terrain == TerrainType.WATER)
            assert not np.any(building_terrain == TerrainType.ROCK)
    
    def test_bsp_generation(self):
        """Test the BSP generation algorithm for building layout."""
        generator = StructureGenerator(width=50, height=50)
        
        # Generate a building using BSP
        building = generator.generate_building(
            x=10, y=10, width=20, height=20, 
            min_room_size=3, structure_type=StructureType.HOUSE,
            seed=42
        )
        
        # Building should have rooms and connections
        assert len(building['rooms']) > 0
        # At least one room per building
        assert len(building['rooms']) >= 1
        # Check that rooms are within building bounds
        for room in building['rooms']:
            rx, ry, rw, rh = room
            assert 10 <= rx < 10 + 20 - rw
            assert 10 <= ry < 10 + 20 - rh
            assert rw >= 3
            assert rh >= 3
    
    def test_structure_connectivity(self):
        """Test that rooms within a building are connected."""
        generator = StructureGenerator(width=50, height=50)
        
        # Generate a multi-room building
        building = generator.generate_building(
            x=5, y=5, width=30, height=30, 
            min_room_size=3, structure_type=StructureType.SHOP,
            seed=123  # Seed that should produce multiple rooms
        )
        
        # If there's only one room, this test is not applicable
        if len(building['rooms']) <= 1:
            pytest.skip("Building has only one room, connectivity not applicable")
            
        # Check that all rooms have connections
        # Count how many corridors connect to each room
        room_connections = {i: 0 for i in range(len(building['rooms']))}
        
        for corridor in building['corridors']:
            from_room, to_room = corridor
            room_connections[from_room] += 1
            room_connections[to_room] += 1
            
        # Every room should have at least one connection
        for room_idx, connection_count in room_connections.items():
            assert connection_count > 0, f"Room {room_idx} has no connections"
    
    def test_map_integration(self):
        """Test integration with the game map."""
        game_map = GameMap(width=100, height=100)
        game_map.generate_terrain(seed=42)
        
        generator = StructureGenerator(width=100, height=100)
        
        # Add buildings to the map
        generator.add_buildings_to_map(game_map, count=5, seed=42)
        
        # Check that structures are properly added to the map
        # We should have entrances marked in the map
        has_entrances = False
        for z in game_map.z_levels:
            if 'entrances' in game_map.z_levels[z]:
                if len(game_map.z_levels[z]['entrances']) > 0:
                    has_entrances = True
                    break
        
        assert has_entrances, "No building entrances found in game map"
    
    def test_artificial_light_sources(self):
        """Test that buildings have artificial light sources."""
        game_map = GameMap(width=100, height=100)
        generator = StructureGenerator(width=100, height=100)
        
        # Add buildings and place artificial lights
        generator.add_buildings_to_map(game_map, count=3, seed=42)
        generator.add_artificial_lights(game_map)
        
        # Set time to night to see effect of artificial lights
        game_map.set_time(hour=22, minute=0)  # 10PM
        
        # Find a building entrance
        entrance_found = False
        entrance_x, entrance_y = 0, 0
        
        for z in game_map.z_levels:
            if 'entrances' in game_map.z_levels[z]:
                for entrance in game_map.z_levels[z]['entrances']:
                    entrance_x, entrance_y = entrance
                    entrance_found = True
                    break
        
        if not entrance_found:
            pytest.skip("No building entrances found")
        
        # Check light levels near entrance - should be higher than ambient night light
        light_level = game_map.get_light_level(entrance_x, entrance_y)
        assert light_level > 0.2, "Building entrance should have artificial light" 